import pytesseract
import pdf2image
from transformers import pipeline
import fitz

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

text = pdf_to_text_without_tables("../pdf_files/example1.pdf")
print(text)
