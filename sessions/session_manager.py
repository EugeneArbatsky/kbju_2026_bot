"""
Менеджер сессий - централизованное управление состояниями пользователей.
"""

from enum import Enum
from typing import Optional, Dict, Any
from telegram.ext import CallbackContext

from .session_types import (
    BaseSession,
    DefaultSession,
    EditingSession,
    OnboardingSession,
    KBJUSetupSession,
    TimezoneSetupSession,
)


class SessionType(Enum):
    """Типы сессий бота"""
    DEFAULT = "default"
    EDITING = "editing"
    ONBOARDING = "onboarding"
    KBJU_SETUP = "kbju_setup"
    TIMEZONE_SETUP = "timezone_setup"


class SessionManager:
    """
    Менеджер сессий пользователей.
    
    Управляет состояниями пользователей и маршрутизирует сообщения
    к соответствующим обработчикам сессий.
    """
    
    # Маппинг типов сессий на классы
    SESSION_CLASSES = {
        SessionType.DEFAULT: DefaultSession,
        SessionType.EDITING: EditingSession,
        SessionType.ONBOARDING: OnboardingSession,
        SessionType.KBJU_SETUP: KBJUSetupSession,
        SessionType.TIMEZONE_SETUP: TimezoneSetupSession,
    }
    
    @staticmethod
    def get_session_type(context: CallbackContext) -> SessionType:
        """
        Определяет текущий тип сессии пользователя.
        
        Args:
            context: Контекст Telegram бота
            
        Returns:
            Тип текущей сессии
        """
        session_type_str = context.user_data.get('session_type')
        
        if not session_type_str:
            return SessionType.DEFAULT
        
        try:
            return SessionType(session_type_str)
        except ValueError:
            return SessionType.DEFAULT
    
    @staticmethod
    def get_session(context: CallbackContext) -> BaseSession:
        """
        Получает объект текущей сессии пользователя.
        
        Args:
            context: Контекст Telegram бота
            
        Returns:
            Объект сессии
        """
        session_type = SessionManager.get_session_type(context)
        session_class = SessionManager.SESSION_CLASSES[session_type]
        return session_class(context)
    
    @staticmethod
    def set_session(
        context: CallbackContext,
        session_type: SessionType,
        session_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Устанавливает новую сессию для пользователя.
        
        Args:
            context: Контекст Telegram бота
            session_type: Тип сессии
            session_data: Дополнительные данные сессии
        """
        context.user_data['session_type'] = session_type.value
        
        if session_data:
            context.user_data.update(session_data)
    
    @staticmethod
    def clear_session(context: CallbackContext) -> None:
        """
        Очищает текущую сессию пользователя, возвращая к дефолтной.
        
        Args:
            context: Контекст Telegram бота
        """
        # Сохраняем только базовые данные пользователя
        session_type = context.user_data.pop('session_type', None)
        
        # Очищаем данные специфичные для сессий
        keys_to_remove = [
            'editing_entry_ids',
            'editing_message_id',
            'editing_day_id',
            'editing_prompt_message_id',
            'onboarding_step',
            'kbju_setup_step',
            'timezone_setup_step',
        ]
        
        for key in keys_to_remove:
            context.user_data.pop(key, None)
        
        # Устанавливаем дефолтную сессию
        SessionManager.set_session(context, SessionType.DEFAULT)
    
    @staticmethod
    def is_in_session(context: CallbackContext, session_type: SessionType) -> bool:
        """
        Проверяет, находится ли пользователь в указанной сессии.
        
        Args:
            context: Контекст Telegram бота
            session_type: Тип сессии для проверки
            
        Returns:
            True если пользователь в указанной сессии
        """
        return SessionManager.get_session_type(context) == session_type
