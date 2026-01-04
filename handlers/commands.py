from telegram import Update
from telegram.ext import CallbackContext
import database

async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.first_name}! 👋\n"
        f"Я бот для подсчета КБЖУ.\n"
        f"Просто напиши мне что-нибудь, и я сохраню это как запись о еде!"
    )

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    help_text = """
🤖 <b>Доступные команды:</b>
/start - Начать диалог
/help - Получить справку
/history - История сообщений
/stats - Статистика
/dbinfo - Информация о базе данных
/nextday - Создать следующий день
/dayresult - Показать записи за текущий день

💡 <b>Просто напиши любое сообщение</b>, и бот сохранит это как запись о еде!
    
📝 <b>Что дальше?</b>
1. Будет команда /add для добавления еды
2. Будет команда /stats для просмотра статистики
3. Будет база данных для хранения твоего прогресса
    """
    await update.message.reply_html(help_text)

async def history_command(update: Update, context: CallbackContext):
    """Показать историю сообщений пользователя"""
    user = update.effective_user
    
    messages = database.get_user_messages(user.id, limit=10)
    
    if not messages:
        await update.message.reply_text(
            "📭 У вас ещё нет сохранённых сообщений.\n"
            "Напишите что-нибудь, и я сохраню это в базу данных!"
        )
        return
    
    response = "📜 Ваша история сообщений:\n\n"
    
    for i, (text, created_at) in enumerate(messages[::-1], 1):
        short_text = text[:30] + "..." if len(text) > 30 else text
        response += f"{i}. {short_text}\n   🕐 {created_at}\n\n"
    
    stats = database.get_message_stats(user.id)
    response += f"📊 Всего сообщений: {stats.get('total_messages', 0)}"
    
    await update.message.reply_text(response)

async def stats_command(update: Update, context: CallbackContext):
    """Показать статистику пользователя"""
    user = update.effective_user
    stats = database.get_message_stats(user.id)
    
    response = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"👤 Имя: {user.first_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📨 Сообщений сохранено: {stats.get('total_messages', 0)}\n"
    )
    
    if stats.get('first_message'):
        response += f"📅 Первое сообщение: {stats['first_message'][:10]}\n"
    if stats.get('last_message'):
        response += f"📅 Последнее сообщение: {stats['last_message'][:10]}\n"
    
    response += f"\n💡 Используйте /history для просмотра истории"
    
    await update.message.reply_html(response)

async def db_info_command(update: Update, context: CallbackContext):
    """Информация о базе данных"""
    import os
    import sqlite3
    db_size = os.path.getsize("kbju_bot.db") if os.path.exists("kbju_bot.db") else 0
    
    response = (
        f"🗄️ <b>Информация о базе данных</b>\n\n"
        f"📁 Файл: kbju_bot.db\n"
        f"📏 Размер: {db_size / 1024:.1f} KB\n"
        f"💾 SQLite версия: {sqlite3.sqlite_version}\n\n"
        f"💡 Все ваши сообщения хранятся локально на этом компьютере.\n"
        f"🔒 Ваши данные в безопасности!"
    )
    
    await update.message.reply_html(response)

async def nextday_command(update: Update, context: CallbackContext):
    """Создать следующий день"""
    user = update.effective_user
    day_id, day_number = database.create_next_day(user.id)
    
    if day_id:
        await update.message.reply_text(
            f"✅ Создан День {day_number}!\n"
            f"Теперь все записи о еде будут относиться к этому дню.\n"
            f"Используйте /dayresult чтобы посмотреть записи за день."
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось создать новый день. Попробуйте позже."
        )

async def dayresult_command(update: Update, context: CallbackContext):
    """Показать записи за текущий день"""
    user = update.effective_user
    
    # Получаем текущий день
    day_id, day_number = database.get_or_create_current_day(user.id)
    
    if not day_id:
        await update.message.reply_text(
            "❌ Не удалось получить информацию о дне."
        )
        return
    
    # Получаем записи о еде за этот день
    entries = database.get_food_entries_for_day(user.id, day_id)
    
    if not entries:
        await update.message.reply_text(
            f"📭 В Дне {day_number} ещё нет записей о еде.\n"
            f"Напишите что-нибудь, и я сохраню это!"
        )
        return
    
    # Формируем ответ в нужном формате
    response = f"📊 <b>День {day_number}</b>\n\n"
    
    for entry_id, message_text, calories, protein, fat, carbs in entries:
        response += (
            f"{entry_id}. {message_text}\n"
            f"{calories} ккал, {protein} белков, {fat} жиров, {carbs} углеводов\n\n"
        )
    
    await update.message.reply_html(response)