import pytesseract
import pdf2image
from transformers import pipeline
import fitz
import cv2
import numpy as np

def text_summary(text: str) -> str:
    """Краткий пересказ данного текста"""
    summarizer = pipeline("summarization", model="IlyaGusev/rut5_base_sum_gazeta")
    result = summarizer(text, max_length=30, min_length=15)
    return result[0]['summary_text']

def pdf_to_text_without_pictures_tables(file_path: str) -> str:
    """Текст из pdf-файла по переданному пути файла
       (работает для файлов без картинок и таблиц)"""
    images = pdf2image.convert_from_path(file_path)
    
    ans = ""
    for i, image in enumerate(images):
        page_text = pytesseract.image_to_string(image, lang='rus+eng')
        ans += f"\n{page_text}\n"
    
    return ans

def pdf_to_text_without_tables(file_path: str) -> str:
    """Текст из pdf-файла по переданному пути файла
       (работает для файлов без таблиц)"""
    ans = ""
    try:
        doc = fitz.open(file_path)
        
        for i, image in enumerate(doc):
            ans += image.get_text() + "\n"
            
        doc.close()
        return ans
    except Exception as e:
        print(f"Ошибка: {e}")
        return ""
    
def pdf_to_test(file_path: str) -> str:
    """Текст из pdf-файла по переданному пути файла"""
    # TODO: Иногда распознаётся текст с картинок. Лучше, чтобы этого не было
    images = pdf2image.convert_from_path(file_path)

    ans = ""
    for i, image in enumerate(images):
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.ones(img.shape[:2], dtype="uint8") * 255

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 100 and h > 50:
                cv2.rectangle(mask, (x, y), (x+w, y+h), 0, -1)

        text = cv2.bitwise_and(gray, gray, mask=mask)
        ans += f"\n{pytesseract.image_to_string(text, lang='rus+eng')}\n"

    return ans

def add_table_schema(text: str) -> str:
    """Добавляет разметку для таблицы по переданному распознанному тексту"""
    response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": "", # Your API key
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
                "text": "У меня есть распознанный из таблицы текст. Помоги мне добавить разметку:\n" + text + \
                        "\n\n" + "Ты должен вернуть только разметку, без каких-либо других комментариев или объяснений."
            },
            ]
        }
        ]
    })
    )
    return response.json()['choices'][0]['message']['content']

text = pdf_to_test("../pdf_files/example1.pdf")
print(text)
