"""
Обработчики сообщений от пользователей.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import database
import texts
from services.food_service import FoodService
from services.user_service import UserService
from services.day_service import DayService
from sessions import SessionManager, SessionType

# Инициализируем сервисы
food_service = FoodService()
user_service = UserService()
day_service = DayService()


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
    """
    Главный обработчик всех текстовых сообщений.
    Маршрутизирует сообщения к соответствующим сессиям.
    """
    user = update.effective_user
    
    # Получаем текущую сессию пользователя
    session = SessionManager.get_session(context)
    
    # Передаем обработку сессии
    handled = await session.handle_message(update, context)
    
    if not handled:
        # Если сессия не обработала сообщение, отправляем сообщение об ошибке
        await update.message.reply_text("Не удалось обработать сообщение. Попробуйте еще раз.")


async def handle_food_message(update: Update, context: CallbackContext):
    """
    Обрабатывает сообщение о еде (используется в DefaultSession).
    """
    user = update.effective_user
    user_message = update.message.text
    
    print(f"📩 Получено сообщение от {user.first_name}: '{user_message}'")
    
    # Сохраняем информацию о пользователе
    user_service.save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Получаем или создаем текущий день
    day_id, day_number = day_service.get_or_create_current_day(user.id)
    
    if not day_id:
        await update.message.reply_text(texts.DATABASE_ERROR_TEXT)
        return
    
    # Показываем статус "печатает"
    await update.message.chat.send_action(action="typing")
    
    # Обрабатываем сообщение через сервис
    dishes = await food_service.process_food_message(user.id, day_id, user_message)
    
    if not dishes:
        await update.message.reply_text(texts.AI_ERROR_TEXT)
        return
    
    print(f"🍽️  Сохранено {len(dishes)} блюд в базу...")
    
    # Получаем количество уже сохраненных блюд за день (для сквозной нумерации)
    existing_count = database.count_food_entries_for_day(user.id, day_id)
    
    # Извлекаем ID сохраненных записей
    saved_ids = [dish.get('id') for dish in dishes if dish.get('id')]
    
    # Формируем ответ с учетом сквозной нумерации
    response = texts.get_food_entries_saved_text(day_number, dishes, start_index=existing_count)
    
    # Создаем кнопки для всего приема пищи
    reply_markup = create_edit_delete_buttons(saved_ids, day_id)
    
    # Отправляем одно сообщение с отчетом и кнопками
    await update.message.reply_text(response, reply_markup=reply_markup)


async def handle_edit_message(update: Update, context: CallbackContext):
    """
    Обрабатывает сообщение в сессии редактирования (используется в EditingSession).
    """
    user = update.effective_user
    user_message = update.message.text
    
    entry_ids = context.user_data.get('editing_entry_ids', [])
    original_message_id = context.user_data.get('editing_message_id')
    day_id = context.user_data.get('editing_day_id')
    
    if not entry_ids or not day_id:
        # Завершаем сессию редактирования если данных нет
        SessionManager.clear_session(context)
        return
    
    # Показываем статус "печатает"
    await update.message.chat.send_action(action="typing")
    
    # Обрабатываем редактирование через сервис
    updated_dishes = await food_service.edit_food_entries(user.id, entry_ids, user_message)
    
    if not updated_dishes:
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
    day_id_current, day_number = day_service.get_or_create_current_day(user.id)
    
    # Получаем количество блюд до этих записей для правильной нумерации
    all_entries = database.get_food_entries_for_day(user.id, day_id)
    start_index = 0
    for e in all_entries:
        if e[0] in entry_ids:
            break
        start_index += 1
    
    updated_text = texts.get_food_entries_saved_text(day_number, updated_dishes, start_index=start_index)
    updated_text += texts.EDIT_UPDATED_SUFFIX
    
    # Кнопки показываются всегда
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
    SessionManager.clear_session(context)


async def delete_dayresult_messages(update: Update, context: CallbackContext, user_id: int):
    """Удаляет все сообщения от бота на команду /dayresult для пользователя"""
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
