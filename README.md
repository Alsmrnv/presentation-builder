# Presentation Builder

Telegram-бот для автоматического создания презентаций из PDF-файлов с использованием технологий RAG (Retrieval-Augmented Generation) и генерации визуализаций.

## Возможности

- **Автоматическое извлечение текста из PDF** с поддержкой OCR
- **Интеллектуальная сегментация** документа на логические части
- **Генерация структуры презентации** с помощью LLM
- **Создание слайдов** с автоматическим форматированием
- **Добавление визуализаций** (графики, диаграммы) на основе контента
- **Извлечение изображений** из исходного PDF и добавление их в презентацию
- **Telegram-интерфейс** для удобной работы

## Требования

- Python 3.8+
- Telegram Bot Token
- OpenRouter API Key (или другой совместимый API ключ)
- Tesseract OCR (для распознавания текста из PDF)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Alsmrnv/presentation-builder.git
cd presentation-builder
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Установите Tesseract OCR:
```bash
sudo apt-get install tesseract-ocr
```

4. Создайте файл `.env` в корне проекта:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
API_KEY=your_openrouter_api_key
```

## Использование

### Запуск Telegram-бота

```bash
cd src/telegram_bot
python3 main.py
```

После запуска бот будет готов к работе. Отправьте ему PDF-файл, и он автоматически создаст презентацию.

### Команды бота

- `/start` - Начать работу с ботом
- `/help` - Показать справку

## Технологии

- **python-telegram-bot** - Telegram Bot API
- **python-pptx** - Создание PowerPoint презентаций
- **pytesseract** - OCR для распознавания текста
- **pdf2image** - Конвертация PDF в изображения
- **sentence-transformers** - Семантический поиск
- **plotly** - Генерация графиков и диаграмм
