from telegram import Update
from telegram.ext import CallbackContext
import database
import texts

async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        texts.get_start_text(user.first_name)
    )

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    await update.message.reply_html(
        texts.HELP_TEXT
    )

async def nextday_command(update: Update, context: CallbackContext):
    """Создать следующий день"""
    user = update.effective_user
    day_id, day_number = database.create_next_day(user.id)
    
    if day_id:
        await update.message.reply_text(
            texts.get_nextday_success_text(day_number)
        )
    else:
        await update.message.reply_text(
            texts.NEXTDAY_ERROR_TEXT
        )

async def dayresult_command(update: Update, context: CallbackContext):
    """Показать записи и итоги за текущий день"""
    user = update.effective_user
    
    # Получаем текущий день
    day_id, day_number = database.get_or_create_current_day(user.id)
    
    if not day_id:
        await update.message.reply_text(
            texts.DAYRESULT_ERROR_TEXT
        )
        return
    
    # Получаем записи о еде за этот день
    entries = database.get_food_entries_for_day(user.id, day_id)
    
    # Получаем итоги за день
    totals = database.get_day_totals(user.id, day_id)
    
    # Формируем ответ
    response = texts.get_dayresult_text(day_number, entries, totals)
    await update.message.reply_html(response)