import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем токен
TOKEN = os.getenv('TELEGRAM_TOKEN')
print(f"🔑 Токен (первые 10 символов): {TOKEN[:10] if TOKEN else 'НЕ НАЙДЕН!'}")

async def start(update: Update, context: CallbackContext):
    """Простой обработчик /start"""
    print(f"📞 Вызвана команда /start от {update.effective_user.first_name}")
    await update.message.reply_text('✅ Бот работает! Простейшая версия.')

async def echo(update: Update, context: CallbackContext):
    """Просто повторяет сообщение"""
    user_text = update.message.text
    print(f"📩 Сообщение от {update.effective_user.first_name}: {user_text}")
    await update.message.reply_text(f'🤖 Вы сказали: {user_text}')

def main():
    print("🚀 Запускаю ТЕСТОВОГО бота...")
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Только две простые команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    print("✅ Тестовый бот запущен!")
    print("📱 Напишите /start в Telegram")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()