"""
Простой модуль для добавления визуализаций к слайдам презентации
"""

import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from .prompts import get_visualization_prompt
from .schemas import validate_llm_response
from .render import render_visualization


def _analyze_slide_for_visualization(slide: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """
    Анализирует один слайд: нужна ли визуализация?
    """
    prompt = f"""
Проанализируй этот слайд презентации и определи, можно ли его данные визуализировать.

ЗАГОЛОВОК: "{slide.get('title', '')}"
ТЕКСТ: "{slide.get('description', '')}"

Есть ли в тексте ЧИСЛА, ПРОЦЕНТЫ, СРАВНЕНИЯ или ТАБЛИЧНЫЕ ДАННЫЕ?
Если ДА - предложи подходящий тип визуализации и извлеки данные.

Возможные типы визуализаций:
- "bar": для сравнения величин (например: Продукт А: 100, Продукт Б: 200)
- "line": для трендов во времени (например: Январь: 100, Февраль: 150)
- "pie": для долей и распределений (например: Доля А: 40%, Доля Б: 60%)
- "table": для структурированных табличных данных
- "scatter": для корреляций
- "histogram": для распределений

Верни ТОЛЬКО JSON в формате:
{{
    "needed": true/false,
    "type": "bar"/"line"/"pie"/"table"/"scatter"/"histogram"/null,
    "data_context": "конкретные числа из текста в формате: Категория1: значение1, Категория2: значение2",
    "chart_title": "предлагаемый заголовок для графика"
}}

Пример для текста "Продажи: Продукт А - 1000 единиц, Продукт Б - 1500 единиц":
{{
    "needed": true,
    "type": "bar",
    "data_context": "Продукт А: 1000, Продукт Б: 1500",
    "chart_title": "Продажи по продуктам"
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
                "messages": [{"role": "user", "content": prompt}],
            }),
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            try:
                content = response_data['choices'][0]['message']['content']
            except KeyError:
                if 'choices' in response_data:
                    content = response_data['choices'][0]['message']['content']
                elif 'response' in response_data:
                    content = response_data['response']
                else:
                    content = ""
            
            cleaned = content.strip()
            for prefix in ['```json', '```']:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].strip()
            
            result = json.loads(cleaned)
            
            if "chart_title" not in result:
                result["chart_title"] = slide.get('title', 'График')
            
            return result
            
    except Exception as e:
        print(f"Ошибка анализа слайда: {e}")
    
    return {
        "needed": False,
        "type": None,
        "data_context": "",
        "chart_title": slide.get('title', 'График')
    }


def _generate_visualization_data(vis_type: str, data_context: str, 
                                chart_title: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Генерирует данные для визуализации через LLM
    """
    try:
        prompt = get_visualization_prompt(vis_type, data_context, chart_title)
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001",
                "messages": [{"role": "user", "content": prompt}],
            }),
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            try:
                content = response_data['choices'][0]['message']['content']
            except KeyError:
                if 'choices' in response_data:
                    content = response_data['choices'][0]['message']['content']
                elif 'response' in response_data:
                    content = response_data['response']
                else:
                    content = ""
            
            cleaned = content.strip()
            for prefix in ['```json', '```']:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].strip()
            
            return json.loads(cleaned)
    except Exception as e:
        print(f"Ошибка генерации данных для {vis_type}: {e}")
    
    return None


def _create_png_visualization(vis_type: str, validated_data: Any, 
                             temp_dir: Path, slide_index: int) -> Optional[str]:
    """
    Создает PNG визуализацию используя новый рендер
    """
    try:
        png_filename = f"slide_{slide_index}_{uuid.uuid4().hex[:8]}.png"
        png_path = temp_dir / png_filename
        
        print(f"    → Создаем PNG...")
        
        try:
            render_visualization(validated_data, png_path)
        except Exception as render_error:
            print(f"    ✗ Ошибка рендеринга: {render_error}")
            return None
        
        if png_path.exists() and png_path.stat().st_size > 0:
            print(f"    ✓ PNG создан: {png_path.name} ({png_path.stat().st_size} байт)")
            return str(png_path)
        else:
            print(f"    ✗ PNG файл не создан или пустой")
            return None
            
    except Exception as e:
        print(f"    ✗ Ошибка создания PNG: {e}")
        return None


def enhance_slides_with_visualizations(
    slides: List[Dict[str, Any]],
    api_key: str,
    temp_dir: str = "temp_visualizations",
    delay: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Основная функция: добавляет PNG визуализации к слайдам
    
    Args:
        slides: список слайдов {title, description}
        api_key: ключ для OpenRouter
        temp_dir: папка для временных PNG файлов
        delay: задержка между запросами к API
    
    Returns:
        Список слайдов с добавленным полем 'visualization' (если нужно)
    """
    enhanced_slides = []
    temp_path = Path(temp_dir)
    temp_path.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print("АНАЛИЗ СЛАЙДОВ НА ВИЗУАЛИЗАЦИИ (PNG)")
    print(f"{'='*60}")
    
    for i, slide in enumerate(slides):
        print(f"\nСлайд {i+1}/{len(slides)}: {slide.get('title', 'Без названия')[:40]}...")
        
        enhanced_slide = slide.copy()
        enhanced_slide["visualization"] = {"needed": False} 
        try:
            analysis = _analyze_slide_for_visualization(slide, api_key)
            
            if analysis.get("needed") and analysis.get("type"):
                vis_type = analysis["type"]
                data_context = analysis.get("data_context", "")
                chart_title = analysis.get("chart_title", slide.get('title', 'График'))
                
                print(f"  → Нужна {vis_type} визуализация: {chart_title}")
                
                time.sleep(delay/2) 
                json_data = _generate_visualization_data(vis_type, data_context, chart_title, api_key)
                
                if json_data:
                    try:
                        validated_data = validate_llm_response(vis_type, json_data)
                        
                        print("  → Создаем PNG визуализацию...")
                        image_path = _create_png_visualization(vis_type, validated_data, temp_path, i+1)
                        
                        if image_path:
                            enhanced_slide["visualization"] = {
                                "needed": True,
                                "type": vis_type,
                                "image_path": image_path,
                                "chart_title": chart_title,
                                "data_context": data_context
                            }
                            print(f" ✓ PNG визуализация добавлена")
                        else:
                            print(f"  ✗ Не удалось создать PNG")
                            enhanced_slide["visualization"] = {"needed": False}
                    
                    except Exception as e:
                        print(f" ✗ Ошибка валидации: {e}")
                        enhanced_slide["visualization"] = {"needed": False}
                
                else:
                    print(f" ✗ Не удалось сгенерировать данные")
                    enhanced_slide["visualization"] = {"needed": False}
            
            else:
                print(f"  → Визуализация не нужна")
        
        except Exception as e:
            print(f"  ✗ Ошибка обработки слайда: {e}")
            enhanced_slide["visualization"] = {"needed": False}
        
        enhanced_slides.append(enhanced_slide)
        
        if i < len(slides) - 1:
            time.sleep(delay/2)  
    
    total_with_vis = sum(1 for s in enhanced_slides if s.get("visualization", {}).get("needed"))
    
    print(f"\n{'='*60}")
    print(f"ГОТОВО! Обработано {len(slides)} слайдов")
    print(f"PNG файлы сохранены в: {temp_path.absolute()}")
    print(f"{'='*60}")
    
    return enhanced_slides