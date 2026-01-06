"""
Обработчики медиа-сообщений (фото, голосовые сообщения).
"""

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
