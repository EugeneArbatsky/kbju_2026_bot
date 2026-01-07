"""
Типы сессий и их обработчики.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import CallbackContext


class BaseSession(ABC):
    """
    Базовый класс для всех сессий.
    
    Каждая сессия определяет, как обрабатывать сообщения пользователя
    в определенном состоянии диалога.
    """
    
    def __init__(self, context: CallbackContext):
        self.context = context
    
    @abstractmethod
    async def handle_message(self, update: Update, context: CallbackContext) -> bool:
        """
        Обрабатывает текстовое сообщение пользователя.
        
        Args:
            update: Обновление от Telegram
            context: Контекст бота
            
        Returns:
            True если сообщение обработано, False если нужно передать дальше
        """
        pass
    
    @abstractmethod
    async def handle_photo(self, update: Update, context: CallbackContext) -> bool:
        """
        Обрабатывает фото от пользователя.
        
        Args:
            update: Обновление от Telegram
            context: Контекст бота
            
        Returns:
            True если фото обработано, False если нужно передать дальше
        """
        pass
    
    @abstractmethod
    async def handle_voice(self, update: Update, context: CallbackContext) -> bool:
        """
        Обрабатывает голосовое сообщение от пользователя.
        
        Args:
            update: Обновление от Telegram
            context: Контекст бота
            
        Returns:
            True если голосовое сообщение обработано, False если нужно передать дальше
        """
        pass


class DefaultSession(BaseSession):
    """
    Дефолтная сессия - ожидание сообщений о еде.
    """
    
    async def handle_message(self, update: Update, context: CallbackContext) -> bool:
        """Обрабатывает текстовое сообщение о еде"""
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from handlers.messages import handle_food_message
        
        await handle_food_message(update, context)
        return True
    
    async def handle_photo(self, update: Update, context: CallbackContext) -> bool:
        """В дефолтной сессии фото пока не обрабатывается"""
        # TODO: Реализовать обработку фото в будущем
        return False
    
    async def handle_voice(self, update: Update, context: CallbackContext) -> bool:
        """Обрабатывает голосовое сообщение о еде"""
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from handlers.media import handle_voice_message
        
        await handle_voice_message(update, context)
        return True


class EditingSession(BaseSession):
    """
    Сессия редактирования записей о еде.
    """
    
    async def handle_message(self, update: Update, context: CallbackContext) -> bool:
        """Обрабатывает сообщение с изменениями"""
        from handlers.messages import handle_edit_message
        
        await handle_edit_message(update, context)
        return True
    
    async def handle_photo(self, update: Update, context: CallbackContext) -> bool:
        """В сессии редактирования фото пока не обрабатывается"""
        return False
    
    async def handle_voice(self, update: Update, context: CallbackContext) -> bool:
        """В сессии редактирования голосовые сообщения пока не обрабатываются"""
        return False


class OnboardingSession(BaseSession):
    """
    Сессия приветствия и онбординга новых пользователей.
    """
    
    async def handle_message(self, update: Update, context: CallbackContext) -> bool:
        """Обрабатывает ответы пользователя в процессе онбординга"""
        # TODO: Реализовать онбординг в будущем
        return False
    
    async def handle_photo(self, update: Update, context: CallbackContext) -> bool:
        """В сессии онбординга фото не обрабатываются"""
        return False
    
    async def handle_voice(self, update: Update, context: CallbackContext) -> bool:
        """В сессии онбординга голосовые сообщения не обрабатываются"""
        return False


class KBJUSetupSession(BaseSession):
    """
    Сессия настройки дневной нормы КБЖУ.
    """
    
    async def handle_message(self, update: Update, context: CallbackContext) -> bool:
        """Обрабатывает ввод нормы КБЖУ"""
        # TODO: Реализовать настройку КБЖУ в будущем
        return False
    
    async def handle_photo(self, update: Update, context: CallbackContext) -> bool:
        """В сессии настройки КБЖУ фото не обрабатываются"""
        return False
    
    async def handle_voice(self, update: Update, context: CallbackContext) -> bool:
        """В сессии настройки КБЖУ голосовые сообщения не обрабатываются"""
        return False


class TimezoneSetupSession(BaseSession):
    """
    Сессия настройки часового пояса.
    """
    
    async def handle_message(self, update: Update, context: CallbackContext) -> bool:
        """Обрабатывает ввод часового пояса"""
        # TODO: Можно перенести логику из команды /timezone сюда
        return False
    
    async def handle_photo(self, update: Update, context: CallbackContext) -> bool:
        """В сессии настройки часового пояса фото не обрабатываются"""
        return False
    
    async def handle_voice(self, update: Update, context: CallbackContext) -> bool:
        """В сессии настройки часового пояса голосовые сообщения не обрабатываются"""
        return False
