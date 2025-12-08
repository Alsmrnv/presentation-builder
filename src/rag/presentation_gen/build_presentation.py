from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_AUTO_SIZE


# def build_presentation(slides, output_pptx: Path):
#     """
#     Создание презентации по слайдам
#     """
#     prs = Presentation()

#     for slide_data in slides:
#         try:
#             slide_layout = prs.slide_layouts[6]
#         except IndexError:
#             slide_layout = prs.slide_layouts[1]
#         slide = prs.slides.add_slide(slide_layout)

#         slide_width = prs.slide_width
#         slide_height = prs.slide_height

#         margin_left = Inches(0.7)
#         margin_right = Inches(0.7)
#         top_margin = Inches(0.5)
#         bottom_margin = Inches(0.7)
#         between = Inches(0.3)
#         title_height = Inches(1.0)

#         title_left = margin_left
#         title_top = top_margin
#         title_width = slide_width - margin_left - margin_right
#         body_left = margin_left
#         body_top = title_top + title_height + between
#         body_width = title_width
#         body_height = slide_height - body_top - bottom_margin

#         title_shape = slide.shapes.add_textbox(title_left, title_top, title_width, title_height)
#         title_tf = title_shape.text_frame
#         title_tf.clear()
#         title_tf.text = slide_data["title"]
#         title_tf.word_wrap = True
#         title_tf.auto_size = MSO_AUTO_SIZE.NONE

#         body_shape = slide.shapes.add_textbox(body_left, body_top, body_width, body_height)
#         tf = body_shape.text_frame
#         tf.clear()
#         tf.text = slide_data["description"]
#         tf.word_wrap = True
#         tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

#         text_len = len(slide_data["description"])
#         if text_len > 800:
#             base_size = 16
#         elif text_len > 500:
#             base_size = 18
#         else:
#             base_size = 22

#         title_size = base_size + 4

#         for paragraph in tf.paragraphs:
#             for run in paragraph.runs:
#                 run.font.size = Pt(base_size)

#         for paragraph in title_tf.paragraphs:
#             for run in paragraph.runs:
#                 run.font.size = Pt(title_size)

#     prs.save(output_pptx.as_posix())


from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
import os


def build_presentation(slides, output_pptx: Path):
    """
    Создание презентации по слайдам с поддержкой визуализаций
    """
    prs = Presentation()

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
            _add_slide_with_visualization(slide, slide_data, slide_width, slide_height)
        else:
            _add_slide_without_visualization(slide, slide_data, slide_width, slide_height)

    prs.save(output_pptx.as_posix())
    print(f"Презентация сохранена: {output_pptx}")


def _add_slide_without_visualization(slide, slide_data, slide_width, slide_height):
    """Добавляет слайд без визуализации"""
    margin_left = Inches(0.7)
    margin_right = Inches(0.7)
    top_margin = Inches(0.5)
    bottom_margin = Inches(0.7)
    between = Inches(0.3)
    title_height = Inches(1.0)

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
    else:
        base_size = 22

    title_size = base_size + 4

    for paragraph in tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(base_size)

    for paragraph in title_tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(title_size)


def _add_slide_with_visualization(slide, slide_data, slide_width, slide_height):
    """Добавляет слайд с визуализацией (текст слева, картинка справа)"""
    margin = Inches(0.5)
    between = Inches(0.3)
    title_height = Inches(0.8)
    
    text_width = slide_width * 0.6
    image_width = slide_width * 0.4 - margin - Inches(0.2)
    
    title_left = margin
    title_top = margin
    title_width = slide_width - 2 * margin
    
    text_left = margin
    text_top = title_top + title_height + between
    text_height = slide_height - text_top - margin
    
    image_left = text_left + text_width + Inches(0.2)
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
    
    text_shape = slide.shapes.add_textbox(text_left, text_top, text_width - margin, text_height)
    text_tf = text_shape.text_frame
    text_tf.clear()
    text_tf.text = slide_data["description"]
    text_tf.word_wrap = True
    text_tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    
    vis_data = slide_data.get("visualization", {})
    image_path = vis_data.get("image_path")
    
    if image_path and Path(image_path).exists():
        try:
            slide.shapes.add_picture(
                str(image_path),
                image_left,
                image_top,
                width=image_width,
                height=image_height
            )
            
            chart_title = vis_data.get("chart_title")
            if chart_title:
                caption_height = Inches(0.4)
                caption_top = image_top + image_height - caption_height
                caption_shape = slide.shapes.add_textbox(
                    image_left, caption_top, image_width, caption_height
                )
                caption_tf = caption_shape.text_frame
                caption_tf.clear()
                caption_tf.text = chart_title
                caption_tf.word_wrap = True
                
                for paragraph in caption_tf.paragraphs:
                    paragraph.alignment = 1  
                    for run in paragraph.runs:
                        run.font.size = Pt(10)
                        run.font.italic = True
        except Exception as e:
            print(f"Ошибка добавления картинки {image_path}: {e}")
    else:
        print(f" Картинка не найдена: {image_path}")
    
    text_len = len(slide_data["description"])
    if text_len > 600:
        base_size = 14
    elif text_len > 400:
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