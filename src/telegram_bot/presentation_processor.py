from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rag.segmenter.window_segmenter import WindowSegmenter
from rag.segmenter.paragraph_segmenter import ParagraphSegmenter
from rag.presentation_gen.slide_generation import create_presentation_plan, generate_slide_descriptions_with_context
from rag.retriever.paragraph_retriever import ParagraphRetriever
from rag.presentation_gen.build_presentation import build_presentation
from visgen.simple_enchancer import enhance_slides_with_visualizations
from text_recognition.pdf_to_text import pdf_to_text


def process_pdf_to_presentation(pdf_path: str, output_dir: str = None) -> str:
    """Обрабатывает PDF-файл и создает презентацию PPTX"""
    load_dotenv()
    
    OPENROUTER_API_KEY = os.getenv("API_KEY")
    if not OPENROUTER_API_KEY:
        raise ValueError("API_KEY не найден в переменных окружения")
    
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="presentation_")
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        text, images_dict = pdf_to_text(pdf_path)
        
        window_segmenter = WindowSegmenter(text)
        chunks = window_segmenter.split()
        
        segmenter = ParagraphSegmenter(text)
        segments = segmenter.split()
        
        retriever = ParagraphRetriever(segments)
        temp_slides = create_presentation_plan(chunks, OPENROUTER_API_KEY)
        relevant_segments = retriever.retrieve_relevant_segments(temp_slides)
        retriever.clear()
        
        slides = create_presentation_plan(chunks, OPENROUTER_API_KEY, relevant_segments)
        
        extracted_images_dir = os.path.join(output_dir, "extracted_images")
        os.makedirs(extracted_images_dir, exist_ok=True)
        
        enhanced_slides = []
        for i, (slide, segment) in enumerate(zip(slides, relevant_segments)):
            slide_has_image = False
            for img_marker in images_dict.keys():
                if img_marker in segment:
                    img_filename = f"slide_{i+1}_{img_marker.replace('[', '').replace(']', '').lower()}.png"
                    img_path = os.path.join(extracted_images_dir, img_filename)
                    images_dict[img_marker].save(img_path)
                    
                    slide_with_image = slide.copy()
                    slide_with_image["visualization"] = {
                        "needed": True,
                        "type": "extracted_image",
                        "image_path": img_path,
                        "chart_title": f"Изображение {img_marker}"
                    }
                    enhanced_slides.append(slide_with_image)
                    slide_has_image = True
                    break
            
            if not slide_has_image:
                enhanced_slides.append(slide)
        
        slides_without_images = []
        for slide in enhanced_slides:
            if not slide.get("visualization", {}).get("needed", False):
                slides_without_images.append(slide)
        
        if slides_without_images:
            vis_dir = os.path.join(output_dir, "presentation_visualizations")
            os.makedirs(vis_dir, exist_ok=True)
            
            generated_visualizations = enhance_slides_with_visualizations(
                slides=slides_without_images,
                api_key=OPENROUTER_API_KEY,
                temp_dir=vis_dir,
                delay=0.2
            )
            
            for i, slide in enumerate(enhanced_slides):
                if not slide.get("visualization", {}).get("needed", False):
                    enhanced_slides[i] = generated_visualizations.pop(0)
        
        has_visualizations = [s.get("visualization", {}).get("needed", False) for s in enhanced_slides]
        updated_slides = generate_slide_descriptions_with_context(
            slides=enhanced_slides,
            relevant_segments=relevant_segments,
            api_key=OPENROUTER_API_KEY,
            has_visualizations=has_visualizations
        )
        
        output_pptx = os.path.join(output_dir, "presentation.pptx")
        build_presentation(updated_slides, Path(output_pptx))
        
        return output_pptx
        
    except Exception as e:
        if output_dir and os.path.exists(output_dir) and output_dir.startswith(tempfile.gettempdir()):
            try:
                shutil.rmtree(output_dir)
            except:
                pass
        raise e
