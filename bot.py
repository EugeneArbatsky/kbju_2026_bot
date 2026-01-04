import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
load_dotenv()  # Загружаем переменные из .env

TOKEN = os.getenv('TELEGRAM_TOKEN') 

async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.first_name}! 👋\n"
        f"Я бот для подсчета КБЖУ.\n"
        f"Просто напиши мне что-нибудь, и я отвечу 'Test Completed!'"
    )

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    help_text = """
🤖 <b>Доступные команды:</b>
/start - Начать диалог
/help - Получить справку

💡 <b>Просто напиши любое сообщение</b>, и бот ответит "Test Completed!"
    
📝 <b>Что дальше?</b>
1. Будет команда /add для добавления еды
2. Будет команда /stats для просмотра статистики
3. Будет база данных для хранения твоего прогресса
    """
    await update.message.reply_html(help_text)

async def handle_message(update: Update, context: CallbackContext):
    """Обработчик всех текстовых сообщений"""
    user_message = update.message.text
    user = update.effective_user
    
    # Вывод в консоль VS Code (удобно для отладки!)
    print(f"📩 Сообщение от {user.first_name} (@{user.username}): {user_message}")
    
    # Отправляем ответ
    await update.message.reply_text(
        f"✅ Test Completed!\n"
        f"Ты написал: '{user_message}'\n\n"
        f"🎯 Следующий шаг: добавим базу данных!"
    )

def main():
    """Запуск бота"""
    print("🚀 Запускаю бота КБЖУ...")
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Обработчик для всех текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("✅ Бот запущен и готов к работе!")
    print("📱 Откройте Telegram и найдите своего бота")
    print("⏸️  Для остановки нажмите Ctrl+C в этом окне")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()