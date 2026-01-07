"""
Обработчики медиа-сообщений (фото, голосовые сообщения).
"""

import os
import tempfile
import asyncio
from telegram import Update
from telegram.ext import CallbackContext
from sessions import SessionManager


async def handle_photo(update: Update, context: CallbackContext):
    """
    Главный обработчик фото.
    Маршрутизирует фото к соответствующим сессиям.
    """
    # Получаем текущую сессию пользователя
    session = SessionManager.get_session(context)
    
    # Передаем обработку сессии
    handled = await session.handle_photo(update, context)
    
    if not handled:
        # Если сессия не обработала фото, отправляем сообщение
        await update.message.reply_text(
            "Обработка фото пока не реализована. "
            "Отправьте текстовое описание того, что вы съели."
        )


async def handle_voice(update: Update, context: CallbackContext):
    """
    Главный обработчик голосовых сообщений.
    Маршрутизирует голосовые сообщения к соответствующим сессиям.
    """
    # Получаем текущую сессию пользователя
    session = SessionManager.get_session(context)
    
    # Передаем обработку сессии
    handled = await session.handle_voice(update, context)
    
    if not handled:
        # Если сессия не обработала голосовое сообщение, отправляем сообщение
        await update.message.reply_text(
            "Обработка голосовых сообщений пока не реализована. "
            "Отправьте текстовое описание того, что вы съели."
        )


async def handle_voice_message(update: Update, context: CallbackContext):
    """
    Обрабатывает голосовое сообщение о еде.
    Скачивает файл, распознает речь, обрабатывает как текстовое сообщение.
    """
    user = update.effective_user
    voice = update.message.voice
    
    print(f"🎤 Получено голосовое сообщение от {user.first_name}")
    import sys
    sys.stdout.flush()
    
    # Показываем статус "печатает" сразу и будем обновлять его периодически
    typing_task = None
    async def keep_typing():
        """Периодически отправляет статус 'печатает'"""
        while True:
            await update.message.chat.send_action(action="typing")
            await asyncio.sleep(3)  # Обновляем каждые 3 секунды
    
    # Запускаем задачу для постоянного показа статуса "печатает"
    typing_task = asyncio.create_task(keep_typing())
    
    # Создаем временный файл для аудио
    temp_file_path = None
    try:
        # Получаем файл голосового сообщения
        voice_file = await context.bot.get_file(voice.file_id)
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            temp_file_path = temp_file.name
        
        # Скачиваем файл
        await voice_file.download_to_drive(temp_file_path)
        
        print(f"📥 Голосовое сообщение скачано: {temp_file_path}")
        
        # Распознаем речь
        from services.speech_service import SpeechService
        speech_service = SpeechService()
        
        print(f"🔍 Начинаю распознавание речи из файла: {temp_file_path}")
        recognized_text = await speech_service.recognize_speech(temp_file_path)
        print(f"🔍 Результат распознавания: {recognized_text}")
        
        # Останавливаем задачу показа статуса перед проверкой результата
        if typing_task:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
        
        if not recognized_text or not recognized_text.strip():
            await update.message.reply_text(
                "Не удалось распознать речь. Попробуйте записать сообщение еще раз или отправьте текстом."
            )
            return
        
        print(f"✅ Распознан текст: '{recognized_text}'")
        import sys
        sys.stdout.flush()
        
        # Обрабатываем распознанный текст напрямую, без изменения update.message
        # Используем ту же логику, что и в handle_food_message, но с нашим текстом
        from services.food_service import FoodService
        from services.user_service import UserService
        from services.day_service import DayService
        from handlers.messages import create_edit_delete_buttons
        import database
        import texts
        
        food_service = FoodService()
        user_service = UserService()
        day_service = DayService()
        
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
        
        # Получаем количество уже сохраненных блюд за день ДО сохранения новых
        existing_count = database.count_food_entries_for_day(user.id, day_id)
        
        # Показываем статус "печатает"
        await update.message.chat.send_action(action="typing")
        
        # Обрабатываем сообщение через сервис
        dishes = await food_service.process_food_message(user.id, day_id, recognized_text)
        
        if not dishes:
            await update.message.reply_text(texts.AI_ERROR_TEXT)
            return
        
        print(f"🍽️  Сохранено {len(dishes)} блюд в базу...")
        import sys
        sys.stdout.flush()
        
        # Извлекаем ID сохраненных записей
        saved_ids = [dish.get('id') for dish in dishes if dish.get('id')]
        
        # Формируем ответ с учетом сквозной нумерации
        response = texts.get_food_entries_saved_text(day_number, dishes, start_index=existing_count)
        
        # Создаем кнопки для всего приема пищи
        reply_markup = create_edit_delete_buttons(saved_ids, day_id)
        
        # Отправляем одно сообщение с отчетом и кнопками
        await update.message.reply_text(response, reply_markup=reply_markup)
        
    except Exception as e:
        print(f"❌ Ошибка при обработке голосового сообщения: {e}")
        # Останавливаем задачу показа статуса при ошибке
        if typing_task:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
        await update.message.reply_text(
            "Произошла ошибка при обработке голосового сообщения. "
            "Попробуйте записать сообщение еще раз или отправьте текстом."
        )
    finally:
        # Удаляем временный файл
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"⚠️  Не удалось удалить временный файл: {e}")
