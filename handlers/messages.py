from telegram import Update
from telegram.ext import CallbackContext
import database
import texts
from ai.service import AIService

ai_service = AIService()

async def handle_message(update: Update, context: CallbackContext):
    """Обработчик всех текстовых сообщений - УПРОЩЕННАЯ ВЕРСИЯ"""
    user = update.effective_user
    user_message = update.message.text
    
    print(f"📩 Получено сообщение от {user.first_name}: '{user_message}'")
    
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
        await update.message.reply_text(texts.DATABASE_ERROR_TEXT)
        return
    
    # Показываем статус "печатает"
    await update.message.chat.send_action(action="typing")
    
    # Получаем анализ от AI (упрощённая версия)
    dishes = await ai_service.analyze_food_text(user_message)
    
    if not dishes:
        await update.message.reply_text(texts.AI_ERROR_TEXT)
        return
    
    print(f"🍽️  Сохраняю {len(dishes)} блюд в базу...")
    
    # Получаем количество уже сохраненных блюд за день (для сквозной нумерации)
    existing_count = database.count_food_entries_for_day(user.id, day_id)
    
    # Сохраняем блюда в базу
    saved_ids = database.save_food_entries(user_id=user.id, day_id=day_id, dishes=dishes)
    
    print(f"✅ Сохранено {len(saved_ids)} записей, IDs: {saved_ids}")
    
    # Формируем ответ с учетом сквозной нумерации
    response = texts.get_food_entries_saved_text(day_number, dishes, start_index=existing_count)
    await update.message.reply_text(response)