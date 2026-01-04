import os
import sqlite3  # Импортируем здесь, а не внутри функции!
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Импортируем нашу базу данных
import database

TOKEN = os.getenv('TELEGRAM_TOKEN')

# ==== ПРОВЕРКА ТОКЕНА ====
if not TOKEN:
    print("❌ ОШИБКА: Токен не найден в .env файле!")
    print("   Убедитесь, что файл .env существует и содержит TELEGRAM_TOKEN")
    exit(1)

print(f"✅ Токен загружен (длина: {len(TOKEN)})")

async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    print(f"👋 /start от {user.first_name}")
    await update.message.reply_html(
        f"Привет, {user.first_name}! 👋\n"
        f"Я бот для подсчета КБЖУ.\n"
        f"Просто напиши мне что-нибудь, и я сохраню это в базу данных!"
    )

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    print(f"📖 /help от {update.effective_user.first_name}")
    help_text = """
🤖 <b>Доступные команды:</b>
/start - Начать диалог
/help - Получить справку
/history - История сообщений
/stats - Статистика
/dbinfo - Информация о базе данных

💡 <b>Просто напиши любое сообщение</b>, и бот сохранит его в базу данных!
    
📝 <b>Что дальше?</b>
1. Будет команда /add для добавления еды
2. Будет команда /stats для просмотра статистики
3. Будет база данных для хранения твоего прогресса
    """
    await update.message.reply_html(help_text)

async def handle_message(update: Update, context: CallbackContext):
    """Обработчик всех текстовых сообщений"""
    user = update.effective_user
    user_message = update.message.text
    
    print(f"💬 Сообщение от {user.first_name}: {user_message}")
    
    # Сохраняем информацию о пользователе
    database.save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Сохраняем сообщение в базу данных
    database.save_message(user.id, user_message)
    
    # Отправляем ответ пользователю
    await update.message.reply_text(
        f"✅ Сообщение сохранено!\n"
        f"📝 Текст: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'\n"
        f"📊 Используй /history чтобы увидеть историю"
    )

async def history_command(update: Update, context: CallbackContext):
    """Показать историю сообщений пользователя"""
    user = update.effective_user
    print(f"📜 /history от {user.first_name}")
    
    # Получаем последние 10 сообщений
    messages = database.get_user_messages(user.id, limit=10)
    
    if not messages:
        await update.message.reply_text(
            "📭 У вас ещё нет сохранённых сообщений.\n"
            "Напишите что-нибудь, и я сохраню это в базу данных!"
        )
        return
    
    # Формируем красивый ответ
    response = "📜 <b>Ваша история сообщений:</b>\n\n"
    
    for i, (text, created_at) in enumerate(messages[::-1], 1):
        # Обрезаем длинные сообщения
        short_text = text[:30] + "..." if len(text) > 30 else text
        # Форматируем дату
        date_str = created_at[:16] if created_at else "неизвестно"
        response += f"{i}. <code>{short_text}</code>\n   🕐 {date_str}\n\n"
    
    # Получаем статистику
    stats = database.get_message_stats(user.id)
    response += f"📊 Всего сообщений: <b>{stats.get('total_messages', 0)}</b>"
    
    await update.message.reply_html(response)

async def stats_command(update: Update, context: CallbackContext):
    """Показать статистику пользователя"""
    user = update.effective_user
    print(f"📊 /stats от {user.first_name}")
    
    stats = database.get_message_stats(user.id)
    
    response = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"👤 Имя: {user.first_name or 'Не указано'}\n"
        f"📛 Юзернейм: @{user.username or 'Не указан'}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📨 Сообщений сохранено: <b>{stats.get('total_messages', 0)}</b>\n"
    )
    
    if stats.get('first_message'):
        response += f"📅 Первое сообщение: {stats['first_message'][:10]}\n"
    if stats.get('last_message'):
        response += f"📅 Последнее сообщение: {stats['last_message'][:10]}\n"
    
    response += f"\n💡 Используйте /history для просмотра истории"
    
    await update.message.reply_html(response)

async def db_info_command(update: Update, context: CallbackContext):
    """Информация о базе данных"""
    print(f"🗄️ /dbinfo от {update.effective_user.first_name}")
    
    db_size = os.path.getsize("kbju_bot.db") if os.path.exists("kbju_bot.db") else 0
    db_exists = os.path.exists("kbju_bot.db")
    
    response = (
        f"🗄️ <b>Информация о базе данных</b>\n\n"
        f"📁 Файл: {'kbju_bot.db' if db_exists else 'Не найден'}\n"
        f"📏 Размер: {db_size / 1024:.1f} KB\n"
        f"💾 SQLite версия: {sqlite3.sqlite_version}\n\n"
        f"💡 Все ваши сообщения хранятся локально на этом компьютере.\n"
        f"🔒 Ваши данные в безопасности!"
    )
    
    await update.message.reply_html(response)

def main():
    """Запуск бота"""
    print("=" * 50)
    print("🚀 Запускаю бота КБЖУ с базой данных")
    print("=" * 50)
    
    # Инициализируем базу данных
    database.init_database()
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("dbinfo", db_info_command))
    
    # Обработчик для всех текстовых сообщений, КРОМЕ команд
    # Используем более простой подход
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("\n✅ Бот запущен и готов к работе!")
    print("💾 База данных SQLite подключена")
    print("📱 Откройте Telegram и найдите своего бота")
    print("💡 Доступные команды: /start, /help, /history, /stats, /dbinfo")
    print("⏸️  Для остановки нажмите Ctrl+C\n")
    
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        print("💡 Проверьте токен в файле .env")

if __name__ == '__main__':
    main()