from telegram import Update
from telegram.ext import CallbackContext
import database
import texts  # Импортируем наши тексты

async def handle_message(update: Update, context: CallbackContext):
    """Обработчик всех текстовых сообщений - теперь сохраняем как запись о еде"""
    user = update.effective_user
    user_message = update.message.text
    
    # Сохраняем информацию о пользователе
    database.save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Получаем или создаем текущий день
    day_id, day_number = database.get_or_create_current_day(user.id)
    
    if not day_id:
        await update.message.reply_text(
            texts.DATABASE_ERROR_TEXT
        )
        return
    
    # Сохраняем сообщение как запись о еде
    database.save_food_entry(user.id, day_id, user_message)
    
    # Отправляем ответ
    await update.message.reply_text(
        texts.get_food_entry_saved_text(day_number, user_message)
    )