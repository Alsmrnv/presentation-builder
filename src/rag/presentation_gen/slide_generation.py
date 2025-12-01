import requests
import json
import time
from typing import List, Dict


def generate_slides_for_chunk(chunk: str, chunk_index: int, chunks_num: int, api_key: str) -> List[Dict]:    
    prompt = f"""
Текст для анализа:
{chunk}
 
Этот текст является {chunk_index + 1}-й частью из {chunks_num} частей большого документа. 

Твоя задача — выделить из этой части **только ключевые, самостоятельные идеи**, достойные вынесения на отдельный слайд. 

КРИТЕРИИ ОТБОРА ИДЕЙ ДЛЯ СЛАЙДА:
    1. Идея должна быть центральной, фундаментальной или отправной точкой для рассуждений.
    2. Идея должна быть логически завершенной в рамках этого фрагмента.
    3. Идея представляет новый концепт, определение, классификацию или вывод, который не был раскрыт ранее.
    4. Идея содержит рекомендации, инструкции, алгоритмы или важные данные.
    5. Слайды должны логически переходить друг в друга

ЧЕГО СЛЕДУЕТ ИЗБЕГАТЬ:
- Не создавай слайды для второстепенных примеров, иллюстраций или уточняющих деталей.
- Не разбивай одну цельную идею на несколько слайдов только для сокращения текста.
- Не создавай слайды-переходы или слайды с формулировками типа "Введение в часть X". Фокус на содержании.

ДЛЯ КАЖДОГО СЛАЙДА УКАЖИ:
- `title`: Яркое и понятное название, отражающее суть идеи.
- `description`: 2-4 предложения, раскрывающие суть идеи. Пиши плотно, по делу.

Верни ответ в формате JSON:
{{
    "slides": [
        {{
            "title": "Название слайда",
            "description": "Описание содержания",
        }}
    ]
}}
"""
    max_attempts = 5
    
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
                content = result['choices'][0]['message']['content']
                
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

def generate_all_slides_plans(chunks: List[str], api_key: str, delay: float = 1.0) -> List[List[Dict]]: 
    slides = []
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        chunk_slides = generate_slides_for_chunk(chunk, i, len(chunks), api_key)
        slides.append(chunk_slides)
        
        if i < len(chunks) - 1:
            time.sleep(delay)
    
    return slides

# def generate_all_slides_plans_parallel(chunks: List[str], api_key: str, max_workers: int = 3) -> List[List[Dict]]:
#     with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#         futures = [
#             executor.submit(generate_slides_for_chunk, chunk, i, len(chunks), api_key)
#             for i, chunk in enumerate(chunks)
#         ]
        
#         slides = []
#         for future in concurrent.futures.as_completed(futures):
#             slides.append(future.result())
    
#     return sorted(slides, key=lambda x: x[0]['chunk_index'] if x else 0)

def merge_slides_plans(slides: List[List[Dict]]) -> List[Dict]:
    merged_slides = []
    
    for chunk_slides in slides:
        merged_slides.extend(chunk_slides)
    
    return merged_slides

def create_presentation_plan(chunks: List[str], api_key: str) -> List[Dict]:
    all_slides_plans = generate_all_slides_plans(chunks, api_key)
    
    final_slides_plan = merge_slides_plans(all_slides_plans)

    return final_slides_plan