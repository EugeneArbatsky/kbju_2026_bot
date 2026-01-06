from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import database
import texts
from ai.service import AIService

ai_service = AIService()

def create_edit_delete_buttons(entry_ids: list, day_id: int, is_current_day: bool = True) -> InlineKeyboardMarkup:
    """Создает кнопки 'Редактировать' и 'Удалить' для приема пищи (список блюд)"""
    # Формируем строку с entry_ids через запятую
    entry_ids_str = ','.join(map(str, entry_ids))
    
    # Формируем callback_data (максимум 64 байта в Telegram)
    edit_callback = f"edit_{entry_ids_str}_{day_id}"
    delete_callback = f"delete_{entry_ids_str}_{day_id}"
    
    # Проверяем длину (Telegram ограничение: 64 байта)
    if len(edit_callback.encode('utf-8')) > 64:
        print(f"⚠️  Callback_data слишком длинный: {len(edit_callback.encode('utf-8'))} байт")
        # Если слишком длинный, используем только первый entry_id (fallback)
        edit_callback = f"edit_{entry_ids[0]}_{day_id}"
        delete_callback = f"delete_{entry_ids[0]}_{day_id}"
        print(f"⚠️  Используем сокращенный формат: {edit_callback}")
    
    keyboard = [
        [
            InlineKeyboardButton("Редактировать", callback_data=edit_callback),
            InlineKeyboardButton("Удалить", callback_data=delete_callback)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_cancel_button() -> InlineKeyboardMarkup:
    """Создает кнопку 'Отменить' для сессии редактирования"""
    keyboard = [[InlineKeyboardButton("Отменить", callback_data="cancel_edit")]]
    return InlineKeyboardMarkup(keyboard)

async def handle_message(update: Update, context: CallbackContext):
    """Обработчик всех текстовых сообщений"""
    user = update.effective_user
    user_message = update.message.text
    
    print(f"📩 Получено сообщение от {user.first_name}: '{user_message}'")
    
    # Проверяем, находится ли пользователь в сессии редактирования
    if 'editing_entry_ids' in context.user_data:
        # Обрабатываем редактирование
        await handle_edit_message(update, context)
        return
    
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
    
    # Получаем анализ от AI
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
    
    # Создаем кнопки для всего приема пищи (всех блюд из этого сообщения)
    # Кнопки показываются всегда, независимо от того, текущий день или нет
    reply_markup = create_edit_delete_buttons(saved_ids, day_id)
    
    # Отправляем одно сообщение с отчетом и кнопками
    await update.message.reply_text(response, reply_markup=reply_markup)

async def handle_edit_message(update: Update, context: CallbackContext):
    """Обрабатывает сообщение в сессии редактирования"""
    user = update.effective_user
    user_message = update.message.text
    
    entry_ids = context.user_data.get('editing_entry_ids', [])
    original_message_id = context.user_data.get('editing_message_id')
    day_id = context.user_data.get('editing_day_id')
    
    if not entry_ids or not day_id:
        return
    
    # Получаем все оригинальные записи
    original_entries = []
    for entry_id in entry_ids:
        entry = database.get_food_entry_by_id(entry_id, user.id)
        if not entry:
            await update.message.reply_text(texts.EDIT_NOT_FOUND_TEXT)
            context.user_data.pop('editing_entry_ids', None)
            context.user_data.pop('editing_message_id', None)
            context.user_data.pop('editing_day_id', None)
            return
        original_entries.append(entry)
    
    # Показываем статус "печатает"
    await update.message.chat.send_action(action="typing")
    
    # Обрабатываем редактирование через AI (весь прием пищи)
    updated_dishes = await ai_service.process_edit_meal(original_entries, user_message)
    
    if not updated_dishes or len(updated_dishes) != len(entry_ids):
        await update.message.reply_text(texts.EDIT_ERROR_TEXT)
        return
    
    # Обновляем все записи в базе данных
    for i, entry_id in enumerate(entry_ids):
        updated_dish = updated_dishes[i]
        success = database.update_food_entry(
            entry_id=entry_id,
            user_id=user.id,
            dish_name=updated_dish['name'],
            calories=updated_dish['calories'],
            protein=updated_dish['protein'],
            fat=updated_dish['fat'],
            carbs=updated_dish['carbs']
        )
        
        if not success:
            await update.message.reply_text(texts.EDIT_ERROR_TEXT)
            return
    
    # Удаляем сообщение с инструкцией "Введите изменения или уточнения"
    prompt_message_id = context.user_data.get('editing_prompt_message_id')
    if prompt_message_id:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=prompt_message_id
            )
        except Exception as e:
            print(f"⚠️  Не удалось удалить сообщение с инструкцией: {e}")
    
    # Отправляем сообщение об успешном обновлении
    await update.message.reply_text(texts.EDIT_SUCCESS_TEXT)
    
    # Формируем обновленный текст сообщения
    # Получаем day_number для форматирования
    day_number = database.get_or_create_current_day(user.id)[1]
    
    # Получаем количество блюд до этих записей для правильной нумерации
    # Подсчитываем количество записей до этой группы (записи отсортированы по created_at)
    all_entries = database.get_food_entries_for_day(user.id, day_id)
    start_index = 0
    for e in all_entries:
        if e[0] in entry_ids:
            break
        start_index += 1
    
    updated_text = texts.get_food_entries_saved_text(day_number, updated_dishes, start_index=start_index)
    updated_text += texts.EDIT_UPDATED_SUFFIX
    
    # Кнопки показываются всегда, независимо от того, текущий день или нет
    reply_markup = create_edit_delete_buttons(entry_ids, day_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=original_message_id,
            text=updated_text,
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"❌ Ошибка при обновлении сообщения: {e}")
    
    # Удаляем сообщения /dayresult
    await delete_dayresult_messages(update, context, user.id)
    
    # Завершаем сессию редактирования
    context.user_data.pop('editing_entry_ids', None)
    context.user_data.pop('editing_message_id', None)
    context.user_data.pop('editing_day_id', None)
    context.user_data.pop('editing_prompt_message_id', None)

async def delete_dayresult_messages(update: Update, context: CallbackContext, user_id: int):
    """Удаляет все сообщения от бота на команду /dayresult для пользователя"""
    # Храним ID сообщений /dayresult в user_data
    if 'dayresult_message_ids' in context.user_data:
        chat_id = update.effective_chat.id
        for msg_id in context.user_data['dayresult_message_ids']:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=msg_id
                )
            except Exception as e:
                # Игнорируем ошибки удаления (сообщение может быть уже удалено)
                print(f"⚠️  Не удалось удалить сообщение {msg_id}: {e}")
        
        context.user_data.pop('dayresult_message_ids', None)