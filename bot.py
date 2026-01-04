import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Импортируем обработчики из наших модулей
from handlers.commands import (
    start, help_command, nextday_command, dayresult_command
)
from handlers.messages import handle_message

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

def main():
    """Запуск бота"""
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
    
    # Обработчик для всех текстовых сообщений, КРОМЕ команд
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(texts.BOT_STARTED_TEXT)
    
    try:
        app.run_polling()
    except Exception as e:
        print(texts.BOT_ERROR_TEXT.format(error=e))

if __name__ == '__main__':
    main()