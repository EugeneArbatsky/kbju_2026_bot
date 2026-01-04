import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Импортируем обработчики из наших модулей
from handlers.commands import (
    start, help_command, history_command, 
    stats_command, db_info_command, nextday_command, dayresult_command
)
from handlers.messages import handle_message

# Загружаем переменные из .env
load_dotenv()

# Импортируем базу данных (она инициализируется автоматически)
import database

TOKEN = os.getenv('TELEGRAM_TOKEN')

# Проверка токена
if not TOKEN:
    print("❌ ОШИБКА: Токен не найден в .env файле!")
    print("   Убедитесь, что файл .env существует и содержит TELEGRAM_TOKEN")
    exit(1)

print(f"✅ Токен загружен (первые 10 символов): {TOKEN[:10]}...")

def main():
    """Запуск бота"""
    print("=" * 50)
    print("🚀 Запускаю бота КБЖУ с системой дней")
    print("=" * 50)
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("dbinfo", db_info_command))
    app.add_handler(CommandHandler("nextday", nextday_command))
    app.add_handler(CommandHandler("dayresult", dayresult_command))
    
    # Обработчик для всех текстовых сообщений, КРОМЕ команд
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("\n✅ Бот запущен и готов к работе!")
    print("💾 База данных SQLite подключена")
    print("📅 Система дней активирована")
    print("📱 Откройте Telegram и найдите своего бота")
    print("💡 Доступные команды:")
    print("   /start, /help, /history, /stats, /dbinfo")
    print("   /nextday - создать следующий день")
    print("   /dayresult - показать записи за текущий день")
    print("⏹️  Для остановки нажмите Ctrl+C\n")
    
    try:
        app.run_polling()
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        print("💡 Проверьте токен в файле .env")

if __name__ == '__main__':
    main()