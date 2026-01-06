"""
Слой сервисов - бизнес-логика приложения.

Сервисы инкапсулируют бизнес-логику и координируют работу
между базой данных, AI сервисом и другими компонентами.
"""

from .food_service import FoodService
from .day_service import DayService
from .user_service import UserService

__all__ = [
    'FoodService',
    'DayService',
    'UserService',
]
