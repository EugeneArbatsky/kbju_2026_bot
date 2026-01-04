from telegram import Update
from telegram.ext import CallbackContext
import database

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
            "❌ Ошибка: не удалось получить текущий день."
        )
        return
    
    # Сохраняем сообщение как запись о еде
    database.save_food_entry(user.id, day_id, user_message)
    
    # Формируем ответ в нужном формате
    response = (
        f"✅ Сообщение сохранено в День {day_number}!\n\n"
        f"📝 {user_message}\n"
        f"400 ккал, 10 белков, 10 жиров, 10 углеводов\n\n"
        f"💡 Используйте /dayresult чтобы посмотреть все записи за день"
    )
    
    await update.message.reply_text(response)