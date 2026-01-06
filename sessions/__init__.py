"""
Система управления сессиями пользователей.

Сессия - это состояние диалога с пользователем, которое определяет,
как бот должен обрабатывать следующие сообщения от пользователя.

Примеры сессий:
- DEFAULT: обычная сессия, ожидание сообщений о еде
- EDITING: сессия редактирования записей
- ONBOARDING: сессия приветствия и онбординга
- KBJU_SETUP: сессия настройки дневной нормы КБЖУ
- TIMEZONE_SETUP: сессия настройки часового пояса
"""

from .session_manager import SessionManager, SessionType
from .session_types import (
    DefaultSession,
    EditingSession,
    OnboardingSession,
    KBJUSetupSession,
    TimezoneSetupSession,
)

__all__ = [
    'SessionManager',
    'SessionType',
    'DefaultSession',
    'EditingSession',
    'OnboardingSession',
    'KBJUSetupSession',
    'TimezoneSetupSession',
]
