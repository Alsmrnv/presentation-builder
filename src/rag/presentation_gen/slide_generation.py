import requests
import json
import time
from typing import List, Dict


prompt_for_big_texts = """
ТВОЯ ЗАДАЧА: Проанализировать часть большого документа и выделить ключевые идеи для слайдов презентации.

ИНСТРУКЦИИ ПО АНАЛИЗУ:
1. Выдели из этой части **только ключевые, самостоятельные идеи**, достойные вынесения на отдельный слайд
2. Слайды должны логически переходить друг в друга

КРИТЕРИИ ОТБОРА ИДЕЙ ДЛЯ СЛАЙДА:
    1. Идея должна быть центральной, фундаментальной или отправной точкой для рассуждений
    2. Идея должна быть логически завершенной в рамках этого фрагмента
    3. Идея представляет новый концепт, определение, классификацию или вывод

ОГРАНИЧЕНИЯ:
- Не создавай слайды для второстепенных примеров, иллюстраций или деталей
- Не разбивай одну цельную идею на несколько слайдов
- Максимум 3 слайда на часть текста

ДЛЯ КАЖДОГО СЛАЙДА УКАЖИ:
- `title`: Яркое и понятное название (до 7 слов)
- `description`: 2-4 предложения, раскрывающие суть идеи согласно предосталенному тексту. Пиши плотно, по делу.

Верни ответ в формате JSON:
{{
    "slides": [
        {{
            "title": "Название слайда",
            "description": "Описание содержания",
        }}
    ]
}}

КОНТЕКСТ:
- Текст ниже является фрагментом большого документа: это {chunk_index}-я часть из {chunks_num} частей документа

ТЕКСТ ДЛЯ АНАЛИЗА:
{chunk}
"""

prompt_for_small_texts = """
ТВОЯ ЗАДАЧА: Проанализировать текст и выделить ключевые идеи для слайдов презентации.

ИНСТРУКЦИИ ПО АНАЛИЗУ:
1. Выдели из этой части **только ключевые, самостоятельные идеи**, достойные вынесения на отдельный слайд
2. Слайды должны логически переходить друг в друга

КРИТЕРИИ ОТБОРА ИДЕЙ ДЛЯ СЛАЙДА:
    1. Идея должна быть центральной, фундаментальной или отправной точкой для рассуждений
    2. Идея должна быть логически завершенной в рамках этого фрагмента
    3. Идея представляет новый концепт, определение, классификацию или вывод

ОГРАНИЧЕНИЯ:
- Не создавай слайды для второстепенных примеров, иллюстраций или деталей
- Не разбивай одну цельную идею на несколько слайдов
- Не более 10 слайдов

РЕЛЕВАНТНЫЕ СЕГМЕНТЫ:
{" ".join(relevant_segments) if relevant_segments else "Нет релевантных сегментов"}

На основе релевантных сегментов и исходного текста создай слайды, используя информацию из релевантных сегментов для наполнения описания слайда.

ДЛЯ КАЖДОГО СЛАЙДА УКАЖИ:
- `title`: Яркое и понятное название (до 7 слов)
- `description`: 2-4 предложения, раскрывающие суть идеи согласно предосталенному тексту. Пиши плотно, по делу.

Верни ответ в формате JSON:
{{
    "slides": [
        {{
            "title": "Название слайда",
            "description": "Описание содержания",
        }}
    ]
}}

ТЕКСТ ДЛЯ АНАЛИЗА:
{chunk}
"""


def generate_slides_for_chunk(chunk: str, chunk_index: int, chunks_num: int, api_key: str) -> List[Dict]:    
    max_attempts = 5

    is_big_text = chunks_num >= 2

    prompt = prompt_for_big_texts.format(chunk_index=chunk_index + 1, chunks_num=chunks_num, chunk=chunk) if is_big_text else prompt_for_small_texts.format(chunk=chunk)
    
    for i in range(max_attempts):
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                })
            )

            if response.status_code == 200:
                result = response.json()
                try:
                    content = result['choices'][0]['message']['content']
                except KeyError:
                    if 'choices' in result:
                        content = result['choices'][0]['message']['content']
                    elif 'response' in result:
                        content = result['response']
                    else:
                        content = ""
                
                print(f"Content type: {type(content)}")
                
                if not content:
                    print(f"Empty response for chunk {chunk_index}")
                    return []

                try:
                    cleaned_content = content.strip()
                    if cleaned_content.startswith('```json'):
                        cleaned_content = cleaned_content[7:]
                    if cleaned_content.startswith('```'):
                        cleaned_content = cleaned_content[3:]
                    if cleaned_content.endswith('```'):
                        cleaned_content = cleaned_content[:-3]
                    
                    cleaned_content = cleaned_content.strip()
                    
                    slides_data = json.loads(cleaned_content)
                    return slides_data.get("slides", [])
                    
                except json.JSONDecodeError as e:
                    print(f"JSON decode error for chunk {chunk_index}: {e}")
                    print(f"Problematic content: {content}")
                    return []
                    
            else:
                print(f"Error loading response for chunk {chunk_index}: {response.status_code}")
                print(f"Answer: {response.text}")
                continue
                
        except Exception as e:
            print(f"Exception raised while processing chunk {chunk_index + 1}: {str(e)}")
            return []

    # raise RuntimeError("Can't reach llm")
    print("Can't reach llm")
    return []


def generate_all_slides_plans(chunks: List[str], api_key: str, delay: float = 0.5, relevant_segments: list = None) -> List[List[Dict]]:
    slides = []
    
    if relevant_segments is None:
        relevant_segments = []
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        chunk_relevant_segments = [relevant_segments[i]] if i < len(relevant_segments) else []
        chunk_slides = generate_slides_for_chunk(chunk, i, len(chunks), api_key, chunk_relevant_segments)
        slides.append(chunk_slides)
        
        # if i < len(chunks) - 1:
        #     time.sleep(delay)
    
    return slides


def generate_slide_descriptions_with_context(slides: List[Dict], relevant_segments: List[str], api_key: str, has_visualizations: List[bool] = None) -> List[Dict]:
    """
    Генерирует описания слайдов с учетом релевантных сегментов и наличия визуализаций
    """
    if has_visualizations is None:
        has_visualizations = [False] * len(slides)
    
    updated_slides = []
    
    for i, (slide, segment, has_vis) in enumerate(zip(slides, relevant_segments, has_visualizations)):
        title = slide.get('title', '')
        original_description = slide.get('description', '')
        
        if has_vis:
            text_volume_instruction = "Текст должен быть кратким, не более 2-3 коротких предложений, так как на слайде будет визуализация."
            max_length = "2-3 коротких предложения"
        else:
            text_volume_instruction = "Текст должен быть более подробным, 4-6 предложений, так как на слайде нет визуализации."
            max_length = "4-6 предложений"
        
        prompt = f"""
РЕЛЕВАНТНЫЙ СЕГМЕНТ:
{segment}

НАЗВАНИЕ СЛАЙДА:
{title}

ПЕРВОНАЧАЛЬНОЕ ОПИСАНИЕ:
{original_description}

Твоя задача - создать новое описание слайда на основе релевантного сегмента и названия слайда.

{text_volume_instruction}

Создай описание, которое:
1. Использует информацию из релевантного сегмента
2. Соответствует названию слайда
3. Имеет объем: {max_length}
4. Логично связано с содержанием

Верни ответ в формате JSON:
{{
    "description": "Новое описание слайда"
}}
"""
        
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                })
            )

            if response.status_code == 200:
                result = response.json()
                try:
                    content = result['choices'][0]['message']['content']
                except KeyError:
                    if 'choices' in result:
                        content = result['choices'][0]['message']['content']
                    elif 'response' in result:
                        content = result['response']
                    else:
                        content = ""
                
                if content:
                    try:
                        cleaned_content = content.strip()
                        if cleaned_content.startswith('```json'):
                            cleaned_content = cleaned_content[7:]
                        if cleaned_content.startswith('```'):
                            cleaned_content = cleaned_content[3:]
                        if cleaned_content.endswith('```'):
                            cleaned_content = cleaned_content[:-3]
                        
                        cleaned_content = cleaned_content.strip()
                        
                        description_data = json.loads(cleaned_content)
                        new_description = description_data.get("description", original_description)
                    except json.JSONDecodeError:
                        new_description = original_description
                else:
                    new_description = original_description
            else:
                new_description = original_description
                
        except Exception:
            new_description = original_description
        
        updated_slide = slide.copy()
        updated_slide['description'] = new_description
        updated_slides.append(updated_slide)
    
    return updated_slides


def merge_slides_plans(slides: List[List[Dict]]) -> List[Dict]:
    merged_slides = []
    
    for chunk_slides in slides:
        merged_slides.extend(chunk_slides)
    
    return merged_slides


def create_presentation_plan(chunks: List[str], api_key: str, relevant_segments: list = None) -> List[Dict]:
    all_slides_plans = generate_all_slides_plans(chunks, api_key, relevant_segments=relevant_segments)
    
    final_slides_plan = merge_slides_plans(all_slides_plans)

    return final_slides_plan
