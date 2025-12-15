from dotenv import load_dotenv
import os

from setup.setup import setup
from rag.segmenter.window_segmenter import WindowSegmenter
from rag.presentation_gen.slide_generation import create_presentation_plan, generate_slide_descriptions_with_context
from rag.segmenter.paragraph_segmenter import ParagraphSegmenter
from rag.retriever.paragraph_retriever import ParagraphRetriever
from rag.presentation_gen.build_presentation import build_presentation
from visgen.simple_enchancer import enhance_slides_with_visualizations
from text_recognition.pdf_to_text import pdf_to_text
from pathlib import Path

def main():
    load_dotenv()

    OPENROUTER_API_KEY = os.getenv("API_KEY")

    text, images_dict = pdf_to_text("./src/pdf_files/example.pdf")

    window_segmenter = WindowSegmenter(text)
    chunks = window_segmenter.split()

    segmenter = ParagraphSegmenter(text)
    segments = segmenter.split()

    retriever = ParagraphRetriever(segments)
    temp_slides = create_presentation_plan(chunks, OPENROUTER_API_KEY)
    relevant_segments = retriever.retrieve_relevant_segments(temp_slides)
    retriever.clear()

    slides = create_presentation_plan(chunks, OPENROUTER_API_KEY, relevant_segments)
    # slides = create_presentation_plan2(temp_slides, OPENROUTER_API_KEY, relevant_segments)
    
    print(f"\n{'='*60}")
    print("ЭТАП: ДОБАВЛЕНИЕ ВИЗУАЛИЗАЦИЙ И ИЗОБРАЖЕНИЙ К СЛАЙДАМ")
    print(f"{'='*60}")
    
    enhanced_slides = []
    for i, (slide, segment) in enumerate(zip(slides, relevant_segments)):
        slide_has_image = False
        for img_marker in images_dict.keys():
            if img_marker in segment:
                img_path = f"extracted_images/slide_{i+1}_{img_marker.replace('[', '').replace(']', '').lower()}.png"
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
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
        generated_visualizations = enhance_slides_with_visualizations(
            slides=slides_without_images,
            api_key=OPENROUTER_API_KEY,
            temp_dir="presentation_visualizations",
            delay=0.2  
        )
        
        for i, slide in enumerate(enhanced_slides):
            if not slide.get("visualization", {}).get("needed", False):
                enhanced_slides[i] = generated_visualizations.pop(0)
    
    vis_count = sum(1 for s in enhanced_slides if s.get("visualization", {}).get("needed"))
    print(f"\n ИТОГО: {vis_count} слайдов из {len(enhanced_slides)} получили визуализации/изображения")
    
    has_visualizations = [s.get("visualization", {}).get("needed", False) for s in enhanced_slides]
    updated_slides = generate_slide_descriptions_with_context(
        slides=enhanced_slides,
        relevant_segments=relevant_segments,
        api_key=OPENROUTER_API_KEY,
        has_visualizations=has_visualizations
    )
    
    build_presentation(updated_slides, Path("presentation_with_visualizations.pptx"))
    
    print(f"\n{'='*60}")
    print("ПРЕЗЕНТАЦИЯ СОЗДАНА!")
    print(f"{'='*60}")
    print(f"Всего слайдов: {len(updated_slides)}")
    print(f"С визуализациями/изображениями: {vis_count}")
    print(f"Без визуализаций: {len(updated_slides) - vis_count}")
    print(f"Файл: presentation_with_visualizations.pptx")
    print(f"{'='*60}")
    
    for i, slide in enumerate(updated_slides):
        print(f"\n--- Слайд {i+1} ---")
        print(f"Заголовок: {slide.get('title', 'No title')}")
        vis = slide.get("visualization", {})
        if vis.get("needed"):
            print(f"Визуализация: {vis.get('type')}")
            print(f"   Файл: {Path(vis.get('image_path', '')).name}")
            print(f"   Заголовок графика: {vis.get('chart_title', '')}")
        else:
            print(f"Без визуализации")
        print(f"Описание: {slide.get('description', 'No description')}")


if __name__ == "__main__":
    setup()
    main()