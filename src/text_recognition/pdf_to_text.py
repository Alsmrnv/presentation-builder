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
    """Проверяет, является ли изображение таблицей"""
    buffered = BytesIO()
    table_image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": API_KEY,
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Посмотри на это изображение. Это таблица? Ответь только 'ДА' если это таблица, или 'НЕТ' если это не таблица (например, график, диаграмма, картинка и т.д.)."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ]
        })
    )
    result = response.json()['choices'][0]['message']['content'].strip().upper()
    return result.startswith('ДА') or result.startswith('YES')
    
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
    
    buffered = BytesIO()
    table_image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    },
    data=json.dumps({
        "model": "google/gemini-2.0-flash-001",
        "messages": [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "У меня есть изображение таблицы. Помоги мне добавить разметку для этой таблицы. Ты должен вернуть только разметку, без каких-либо других комментариев или объяснений."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}"
                }
            }
            ]
        }
        ]
    })
    )
    return response.json()['choices'][0]['message']['content']

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

# print(pdf_to_text("../pdf_files/example1.pdf"))
