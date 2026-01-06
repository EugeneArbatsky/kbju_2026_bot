"""
Сервис для работы с пользователями.
"""

from typing import Optional
import database


class UserService:
    """Сервис для работы с пользователями"""
    
    def save_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str]
    ) -> bool:
        """
        Сохраняет информацию о пользователе.
        
        Args:
            user_id: ID пользователя
            username: Имя пользователя
            first_name: Имя
            last_name: Фамилия
            
        Returns:
            True если сохранение успешно
        """
        return database.save_user(user_id, username, first_name, last_name)
    
    def get_timezone(self, user_id: int) -> str:
        """
        Получает часовой пояс пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Название часового пояса
        """
        return database.get_user_timezone(user_id)
    
    def set_timezone(self, user_id: int, timezone: str) -> bool:
        """
        Устанавливает часовой пояс пользователя.
        
        Args:
            user_id: ID пользователя
            timezone: Название часового пояса
            
        Returns:
            True если установка успешна
        """
        return database.set_user_timezone(user_id, timezone)
