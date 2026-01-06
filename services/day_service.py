"""
Сервис для работы с днями.
"""

from typing import Tuple, Optional, Dict, Any
import database


class DayService:
    """Сервис для работы с днями пользователей"""
    
    def get_or_create_current_day(self, user_id: int) -> Tuple[Optional[int], Optional[int]]:
        """
        Получает или создает текущий день пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Кортеж (day_id, day_number) или (None, None) в случае ошибки
        """
        return database.get_or_create_current_day(user_id)
    
    def create_next_day(self, user_id: int) -> Tuple[Optional[int], Optional[int]]:
        """
        Создает следующий день для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Кортеж (day_id, day_number) или (None, None) в случае ошибки
        """
        return database.create_next_day(user_id)
    
    def get_day_result(self, user_id: int, day_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает результаты за день.
        
        Args:
            user_id: ID пользователя
            day_id: ID дня
            
        Returns:
            Словарь с записями и итогами или None в случае ошибки
        """
        entries = database.get_food_entries_for_day(user_id, day_id)
        totals = database.get_day_totals(user_id, day_id)
        
        # Получаем day_number
        # Для этого нужно получить информацию о дне
        # Пока возвращаем то что есть
        return {
            'entries': entries,
            'totals': totals
        }
