import os
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Импортируем обработчики из наших модулей
from handlers.commands import (
    start, help_command, nextday_command, dayresult_command, timezone_command
)
from handlers.messages import handle_message
from handlers.callbacks import handle_callback

# Импортируем тексты
import texts

# Загружаем переменные из .env
load_dotenv()

# Импортируем базу данных (она инициализируется автоматически)
import database

TOKEN = os.getenv('TELEGRAM_TOKEN')

# Проверка токена
if not TOKEN:
    print(texts.TOKEN_ERROR_TEXT)
    exit(1)

print(texts.get_token_loaded_text(TOKEN[:10]))

async def main():
    """Асинхронный запуск бота"""
    print(texts.BOT_START_HEADER)
    print(texts.BOT_START_TITLE)
    print(texts.BOT_START_FOOTER)
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("nextday", nextday_command))
    app.add_handler(CommandHandler("dayresult", dayresult_command))
    app.add_handler(CommandHandler("timezone", timezone_command))
    
    # Обработчик callback кнопок (должен быть перед обработчиком сообщений)
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Обработчик для всех текстовых сообщений, КРОМЕ команд
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(texts.BOT_STARTED_TEXT)
    
    try:
        # Запускаем бота
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=None)
        
        # Бесконечный цикл
        await asyncio.Event().wait()
        
    except Exception as e:
        print(texts.BOT_ERROR_TEXT.format(error=e))
    finally:
        # Корректное завершение
        if 'app' in locals():
            await app.stop()
            await app.shutdown()

if __name__ == '__main__':
    # Запускаем асинхронную функцию
    asyncio.run(main())