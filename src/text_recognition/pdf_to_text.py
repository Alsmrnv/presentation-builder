import pytesseract
import pdf2image
# from transformers import pipeline
# import fitz
import cv2
import numpy as np
import requests
import json
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# def text_summary(text: str) -> str:
#     """Краткий пересказ данного текста"""
#     summarizer = pipeline("summarization", model="IlyaGusev/rut5_base_sum_gazeta")
#     result = summarizer(text, max_length=30, min_length=15)
#     return result[0]['summary_text']

# def pdf_to_text_without_pictures_tables(file_path: str) -> str:
#     """Текст из pdf-файла по переданному пути файла
#        (работает для файлов без картинок и таблиц)"""
#     images = pdf2image.convert_from_path(file_path)
    
#     ans = ""
#     for i, image in enumerate(images):
#         page_text = pytesseract.image_to_string(image, lang='rus+eng')
#         ans += f"\n{page_text}\n"
    
#     return ans

# def pdf_to_text_without_tables(file_path: str) -> str:
#     """Текст из pdf-файла по переданному пути файла
#        (работает для файлов без таблиц)"""
#     ans = ""
#     try:
#         doc = fitz.open(file_path)
        
#         for i, image in enumerate(doc):
#             ans += image.get_text() + "\n"
            
#         doc.close()
#         return ans
#     except Exception as e:
#         print(f"Ошибка: {e}")
#         return ""

def check_if_table(table_image: Image.Image) -> bool:
    """Проверяет, является ли изображение таблицей. Используем упрощенную эвристику для ускорения."""
    
    import cv2
    import numpy as np
    
    opencv_image = cv2.cvtColor(np.array(table_image), cv2.COLOR_RGB2GRAY)
    
    _, thresh = cv2.threshold(opencv_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
    
    horizontal_count = cv2.countNonZero(horizontal_lines)
    vertical_count = cv2.countNonZero(vertical_lines)
    
    return horizontal_count > 50 and vertical_count > 50 
    
def image_to_text_without_pictures_and_tables(image, start_idx: int = 0) -> tuple[str, list, int]:
    """Текст из pdf-файла по переданному пути файла. Картинки и таблицы игнорируются"""
    # TODO: Иногда распознаётся текст с картинок. Лучше, чтобы этого не было
    ans = "" 
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.ones(gray.shape[:2], dtype="uint8") * 255

    masked_regions = []
    region_idx = start_idx
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 100 and h > 50:
            cv2.rectangle(mask, (x, y), (x+w, y+h), 0, -1)
            region_idx += 1
            masked_regions.append((x, y, w, h, region_idx))

    text = cv2.bitwise_and(gray, gray, mask=mask)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.2
    thickness = 3
    
    for x, y, w, h, idx in masked_regions:
        cv2.rectangle(text, (x, y), (x+w, y+h), 255, -1)
        
        marker_text = f"[IMAGE_{idx}]"
        (text_width, text_height), _ = cv2.getTextSize(marker_text, font, font_scale, thickness)
        text_x = x + (w - text_width) // 2
        text_y = y + (h + text_height) // 2
        
        cv2.putText(text, marker_text, (text_x, text_y), 
                    font, font_scale, 0, thickness)
    
    ans += f"\n{pytesseract.image_to_string(text, lang='rus+eng')}\n"

    return ans, region_idx

def image_to_text_from_tables(image, start_idx: int = 0) -> tuple[dict, int]:
    """Извлекает таблицы и картинки из pdf-файла"""
    ans = {}
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    region_idx = start_idx
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 100 and h > 50:
            region_idx += 1
            table_region = image.crop((x, y, x + w, y + h))
            key = f"[IMAGE_{region_idx}]"
            ans[key] = table_region
    
    return ans, region_idx

def add_table_schema(table_image: Image.Image) -> str:
    """Добавляет разметку для таблицы по переданному изображению таблицы"""
    if not check_if_table(table_image):
        return ""
    
    
    import cv2
    import numpy as np
    from PIL import Image
    
    opencv_image = cv2.cvtColor(np.array(table_image), cv2.COLOR_RGB2GRAY)
    
    _, thresh = cv2.threshold(opencv_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    try:
        import pytesseract
        table_text = pytesseract.image_to_string(thresh, lang='rus+eng')
        
        if table_text.strip():
            return f"Таблица:\n{table_text}"
        else:
            return "[ТАБЛИЦА]"
    except:
        return "[ТАБЛИЦА]"

def pdf_to_text(pdf_path: str) -> tuple[str, dict]:
    """Возвращает распознанный текст с маркерами изображений (IMAGE_i) и словарь изображений с ключами в виде маркеров.
       Таблицы заменяются на их разметку и маркеры, картинки остаются как маркеры"""
    images = pdf2image.convert_from_path(pdf_path)
    ans = ""
    images_dict = {}
    global_image_idx = 0

    for i, image in enumerate(images):
        text_without_tables, next_idx = image_to_text_without_pictures_and_tables(image, global_image_idx)
        tables_dict, next_idx2 = image_to_text_from_tables(image, global_image_idx)
        
        global_image_idx = max(next_idx, next_idx2)

        for key, table_image in tables_dict.items():
            images_dict[key] = table_image
            processed_table = add_table_schema(table_image)
            text_without_tables = text_without_tables.replace(key, f"{processed_table}\n{key}")
        
        ans += text_without_tables
    
    return ans, images_dict

