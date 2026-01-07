"""
Сервис для работы с едой и записями о еде.
"""

from typing import List, Dict, Any, Optional
import database
from ai.service import AIService


class FoodService:
    """Сервис для работы с записями о еде"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    async def process_food_message(
        self,
        user_id: int,
        day_id: int,
        message_text: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Обрабатывает сообщение пользователя о еде.
        
        Args:
            user_id: ID пользователя
            day_id: ID дня
            message_text: Текст сообщения пользователя
            
        Returns:
            Список сохраненных записей о еде или None в случае ошибки
        """
        # Анализируем текст через AI
        dishes = await self.ai_service.analyze_food_text(message_text)
        
        if not dishes:
            return None
        
        # Сохраняем в базу данных
        saved_ids = database.save_food_entries(user_id, day_id, dishes)
        
        if not saved_ids:
            return None
        
        # Возвращаем сохраненные блюда с их ID
        result = []
        for i, dish in enumerate(dishes):
            result.append({
                **dish,
                'id': saved_ids[i] if i < len(saved_ids) else None
            })
        
        return result
    
    async def edit_food_entries(
        self,
        user_id: int,
        entry_ids: List[int],
        edit_text: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Редактирует записи о еде.
        
        Args:
            user_id: ID пользователя
            entry_ids: Список ID записей для редактирования
            edit_text: Текст с изменениями
            
        Returns:
            Список обновленных записей или None в случае ошибки
        """
        # Получаем оригинальные записи
        original_entries = []
        for entry_id in entry_ids:
            entry = database.get_food_entry_by_id(entry_id, user_id)
            if not entry:
                return None
            original_entries.append(entry)
        
        # Обрабатываем редактирование через AI
        updated_dishes = await self.ai_service.process_edit_meal(original_entries, edit_text)
        
        if not updated_dishes or len(updated_dishes) != len(entry_ids):
            return None
        
        # Обновляем записи в базе данных
        for i, entry_id in enumerate(entry_ids):
            updated_dish = updated_dishes[i]
            success = database.update_food_entry(
                entry_id=entry_id,
                user_id=user_id,
                dish_name=updated_dish['name'],
                calories=updated_dish['calories'],
                protein=updated_dish['protein'],
                fat=updated_dish['fat'],
                carbs=updated_dish['carbs'],
                grams=updated_dish['grams']
            )
            
            if not success:
                return None
        
        return updated_dishes
    
    def delete_food_entries(self, user_id: int, entry_ids: List[int]) -> bool:
        """
        Удаляет записи о еде.
        
        Args:
            user_id: ID пользователя
            entry_ids: Список ID записей для удаления
            
        Returns:
            True если удаление успешно
        """
        return database.delete_food_entries(entry_ids, user_id)
