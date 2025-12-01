from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_AUTO_SIZE


def build_presentation(slides, output_pptx: Path):
    """
    Создание презентации по слайдам
    """
    prs = Presentation()

    for slide_data in slides:
        try:
            slide_layout = prs.slide_layouts[6]
        except IndexError:
            slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)

        slide_width = prs.slide_width
        slide_height = prs.slide_height

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

    prs.save(output_pptx.as_posix())