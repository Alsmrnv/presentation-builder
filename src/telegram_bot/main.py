import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

from setup.setup import setup
from presentation_processor import process_pdf_to_presentation

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения. Добавьте его в .env файл.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_message = """
👋 Привет! Я бот для создания презентаций из PDF-файлов.

📋 Как использовать:
1. Отправьте мне PDF-файл
2. Я обработаю его и создам презентацию PPTX
3. Получите готовую презентацию!

⚠️ Обработка может занять некоторое время, пожалуйста, подождите.
"""
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 Справка по использованию бота:

/start - Начать работу с ботом
/help - Показать эту справку

Просто отправьте PDF-файл боту, и он создаст из него презентацию!

💡 Советы:
• Файл должен быть в формате PDF
• Обработка может занять несколько минут
• Результат будет отправлен в формате PPTX
"""
    await update.message.reply_text(help_text)


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик загрузки PDF-файлов"""
    user = update.effective_user
    chat = update.effective_chat
    
    if not update.message.document:
        await update.message.reply_text("❌ Пожалуйста, отправьте PDF-файл как документ.")
        return
    
    document = update.message.document
    
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Файл должен быть в формате PDF (.pdf)")
        return
    
    status_message = await update.message.reply_text("⏳ Начинаю обработку файла...")
    
    temp_dir = tempfile.mkdtemp(prefix="telegram_presentation_")
    pdf_path = None
    pptx_path = None
    
    try:
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.UPLOAD_DOCUMENT)
        
        file = await context.bot.get_file(document.file_id)
        pdf_path = os.path.join(temp_dir, document.file_name)
        await file.download_to_drive(pdf_path)
        
        logger.info(f"Файл {document.file_name} загружен пользователем {user.id}")
        
        await status_message.edit_text("⏳ Обрабатываю PDF-файл. Это может занять несколько минут...")
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            pptx_path = await loop.run_in_executor(
                executor,
                process_pdf_to_presentation,
                pdf_path,
                temp_dir
            )
        
        await status_message.edit_text("✅ Презентация готова! Отправляю файл...")
        
        with open(pptx_path, 'rb') as pptx_file:
            await update.message.reply_document(
                document=pptx_file,
                filename=f"presentation_{Path(document.file_name).stem}.pptx",
                caption="🎉 Ваша презентация готова!"
            )
        
        await status_message.delete()
        logger.info(f"Презентация успешно создана и отправлена пользователю {user.id}")
        
    except ValueError as e:
        error_msg = f"❌ Ошибка конфигурации: {str(e)}"
        await status_message.edit_text(error_msg)
        logger.error(f"Ошибка конфигурации для пользователя {user.id}: {e}")
        
    except Exception as e:
        error_msg = f"❌ Произошла ошибка при обработке файла: {str(e)}"
        await status_message.edit_text(error_msg)
        logger.error(f"Ошибка при обработке файла для пользователя {user.id}: {e}", exc_info=True)
        
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Временная директория {temp_dir} удалена")
            except Exception as e:
                logger.warning(f"Не удалось удалить временную директорию {temp_dir}: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    await update.message.reply_text(
        "📎 Пожалуйста, отправьте PDF-файл для создания презентации.\n"
        "Используйте /help для получения справки."
    )


def main():
    """Запуск бота"""
    setup()
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("Бот запущен и готов к работе")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
