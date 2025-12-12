from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_AUTO_SIZE



def build_presentation(slides, output_pptx: Path):
    """
    Создание презентации по слайдам с поддержкой визуализаций
    """
    prs = Presentation()
    
    prs.slide_width = Inches(13.33) 
    prs.slide_height = Inches(7.5)   

    for slide_data in slides:
        has_visualization = slide_data.get("visualization", {}).get("needed", False)
        
        if has_visualization:
            slide_layout = prs.slide_layouts[6]  
        else:
            try:
                slide_layout = prs.slide_layouts[6]
            except IndexError:
                slide_layout = prs.slide_layouts[1]
        
        slide = prs.slides.add_slide(slide_layout)
        slide_width = prs.slide_width
        slide_height = prs.slide_height

        if has_visualization:
            vis_data = slide_data.get("visualization", {})
            vis_type = vis_data.get("type", "")
            
            aspect_ratios = {
                "line": 50/350, 
                "bar": 500/350,   
                "pie": 450/350,  
                "scatter": 550/350,
                "histogram": 550/350, 
                "table": 700/400
            }
            
            vis_aspect_ratio = aspect_ratios.get(vis_type, 1.0)
            
            if vis_aspect_ratio >= 1.3: 
                _add_slide_with_horizontal_visualization(slide, slide_data, slide_width, slide_height)
            else:
                _add_slide_with_vertical_visualization(slide, slide_data, slide_width, slide_height)
        else:
            _add_slide_full_text(slide, slide_data, slide_width, slide_height)

    prs.save(output_pptx.as_posix())
    print(f"✅ Презентация сохранена: {output_pptx}")




def _add_slide_full_text(slide, slide_data, slide_width, slide_height):
    """Добавляет слайд с полноразмерным текстом (когда нет визуализации)"""
    margin_left = Inches(0.8)
    margin_right = Inches(0.8)
    top_margin = Inches(0.6)
    bottom_margin = Inches(0.8)
    between = Inches(0.3)
    title_height = Inches(0.9)

    title_left = margin_left
    title_top = top_margin
    title_width = slide_width - margin_left - margin_right
    body_left = margin_left
    body_top = title_top + title_height + between
    body_width = title_width
    body_height = slide_height - body_top - bottom_margin

    title_shape = slide.shapes.add_textbox(title_left, title_top, title_width, title_height)
    title_tf = title_shape.text_frame
    title_tf.clear()
    title_tf.text = slide_data["title"]
    title_tf.word_wrap = True
    title_tf.auto_size = MSO_AUTO_SIZE.NONE
    
    for paragraph in title_tf.paragraphs:
        paragraph.alignment = 1 
    body_shape = slide.shapes.add_textbox(body_left, body_top, body_width, body_height)
    tf = body_shape.text_frame
    tf.clear()
    tf.text = slide_data["description"]
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

    text_len = len(slide_data["description"])
    if text_len > 800:
        base_size = 16   
    elif text_len > 500:
        base_size = 18   
    elif text_len > 300:
        base_size = 20   
    else:
        base_size = 22   

    title_size = base_size + 2

    for paragraph in tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(base_size)

    for paragraph in title_tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(title_size)
            run.font.bold = True


def _add_slide_with_vertical_visualization(slide, slide_data, slide_width, slide_height):
    """Добавляет слайд с вертикальной визуализацией (рядом с текстом)"""
    margin = Inches(0.5)
    between = Inches(0.3)
    title_height = Inches(0.7)
    
    vis_data = slide_data.get("visualization", {})
    vis_type = vis_data.get("type", "")
    
    text_width = slide_width * 0.5 - margin
    image_width = slide_width * 0.5 - margin
    text_left = margin
    image_left = text_left + text_width + between
    
    title_left = margin
    title_top = margin
    title_width = slide_width - 2 * margin
    
    text_top = title_top + title_height + between
    text_height = slide_height - text_top - margin
    image_top = text_top
    image_height = text_height
    
    title_shape = slide.shapes.add_textbox(title_left, title_top, title_width, title_height)
    title_tf = title_shape.text_frame
    title_tf.clear()
    title_tf.text = slide_data["title"]
    title_tf.word_wrap = True
    title_tf.auto_size = MSO_AUTO_SIZE.NONE
    
    for paragraph in title_tf.paragraphs:
        paragraph.alignment = 1

    text_shape = slide.shapes.add_textbox(text_left, text_top, text_width, text_height)
    text_tf = text_shape.text_frame
    text_tf.clear()
    text_tf.text = slide_data["description"]
    text_tf.word_wrap = True
    text_tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    
    text_len = len(slide_data["description"])
    if text_len > 800:
        base_size = 12
    elif text_len > 500:
        base_size = 14
    elif text_len > 300:
        base_size = 16
    else:
        base_size = 18

    title_size = base_size + 2
    
    for paragraph in text_tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(base_size)
    
    for paragraph in title_tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(title_size)
            run.font.bold = True
    
    image_path = vis_data.get("image_path")
    
    if image_path and Path(image_path).exists():
        try:
            from PIL import Image
            img = Image.open(image_path)
            img_width, img_height = img.size
            img_aspect = img_width / img_height
            
            available_aspect = image_width / image_height
            
            if img_aspect > available_aspect:
                final_width = image_width
                final_height = image_width / img_aspect
            else:
                final_height = image_height
                final_width = image_height * img_aspect
            
            img_left = image_left + (image_width - final_width) / 2
            img_top = image_top + (image_height - final_height) / 2
            
            slide.shapes.add_picture(
                str(image_path),
                img_left,
                img_top,
                width=final_width,
                height=final_height
            )
            
            chart_title = vis_data.get("chart_title")
            if chart_title:
                caption_height = Inches(0.3)
                caption_top = img_top + final_height + Inches(0.05) 
                caption_shape = slide.shapes.add_textbox(
                    image_left, caption_top, final_width, caption_height
                )
                caption_tf = caption_shape.text_frame
                caption_tf.clear()
                caption_tf.text = chart_title
                caption_tf.word_wrap = True
                
                for paragraph in caption_tf.paragraphs:
                    paragraph.alignment = 1
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
                        run.font.italic = True
                        
        except Exception as e:
            print(f"Ошибка добавления картинки {image_path}: {e}")
            error_shape = slide.shapes.add_textbox(
                image_left, image_top, image_width, Inches(0.3)
            )
            error_tf = error_shape.text_frame
            error_tf.text = "Ошибка изображения"
            for paragraph in error_tf.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(8)
    else:
        print(f"Картинка не найдена: {image_path}")


def _add_slide_with_horizontal_visualization(slide, slide_data, slide_width, slide_height):
    """Добавляет слайд с горизонтальной визуализацией (под текстом)"""
    margin = Inches(0.5)
    between = Inches(0.3)
    title_height = Inches(0.7)
    
    vis_data = slide_data.get("visualization", {})
    vis_type = vis_data.get("type", "")
    
    title_left = margin
    title_top = margin
    title_width = slide_width - 2 * margin
    
    text_left = margin
    text_top = title_top + title_height + between
    text_width = title_width
    
    title_shape = slide.shapes.add_textbox(title_left, title_top, title_width, title_height)
    title_tf = title_shape.text_frame
    title_tf.clear()
    title_tf.text = slide_data["title"]
    title_tf.word_wrap = True
    title_tf.auto_size = MSO_AUTO_SIZE.NONE
    
    for paragraph in title_tf.paragraphs:
        paragraph.alignment = 1

    text_shape = slide.shapes.add_textbox(text_left, text_top, text_width, Inches(1.5))
    text_tf = text_shape.text_frame
    text_tf.clear()
    text_tf.text = slide_data["description"]
    text_tf.word_wrap = True
    text_tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    
    text_len = len(slide_data["description"])
    if text_len > 800:
        base_size = 12
    elif text_len > 500:
        base_size = 14
    elif text_len > 300:
        base_size = 16
    else:
        base_size = 18

    title_size = base_size + 2

    for paragraph in text_tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(base_size)

    for paragraph in title_tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(title_size)
            run.font.bold = True
    
    text_shape_height = min(Inches(2.0), slide_height - title_top - title_height - between - Inches(2.0))  # Limit text height
    image_top = text_top + text_shape_height + between
    image_left = margin
    image_width = slide_width - 2 * margin
    image_height = slide_height - image_top - margin
    
    image_path = vis_data.get("image_path")
    
    if image_path and Path(image_path).exists():
        try:
            from PIL import Image
            img = Image.open(image_path)
            img_width, img_height = img.size
            img_aspect = img_width / img_height
            
            available_aspect = image_width / image_height
            
            if img_aspect > available_aspect: 
                final_width = image_width
                final_height = image_width / img_aspect
            else: 
                final_height = image_height
                final_width = image_height * img_aspect
            
            img_left = image_left + (image_width - final_width) / 2
            img_top = image_top + (image_height - final_height) / 2
            
            slide.shapes.add_picture(
                str(image_path),
                img_left,
                img_top,
                width=final_width,
                height=final_height
            )
            
            chart_title = vis_data.get("chart_title")
            if chart_title:
                caption_height = Inches(0.3)
                caption_top = img_top + final_height + Inches(0.05) 
                caption_shape = slide.shapes.add_textbox(
                    img_left, caption_top, final_width, caption_height
                )
                caption_tf = caption_shape.text_frame
                caption_tf.clear()
                caption_tf.text = chart_title
                caption_tf.word_wrap = True
                
                for paragraph in caption_tf.paragraphs:
                    paragraph.alignment = 1
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
                        run.font.italic = True
                        
        except Exception as e:
            print(f"Ошибка добавления картинки {image_path}: {e}")
            error_shape = slide.shapes.add_textbox(
                image_left, image_top, image_width, Inches(0.3)
            )
            error_tf = error_shape.text_frame
            error_tf.text = "Ошибка изображения"
            for paragraph in error_tf.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(8)
    else:
        print(f"Картинка не найдена: {image_path}")