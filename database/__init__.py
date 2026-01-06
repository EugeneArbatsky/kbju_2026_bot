"""
Модуль работы с базой данных.

Разделен на подмодули по доменам:
- users: работа с пользователями
- days: работа с днями
- food_entries: работа с записями о еде
"""

from .connection import get_connection, init_database
from .users import (
    save_user,
    get_user_timezone,
    set_user_timezone,
)
from .days import (
    get_or_create_current_day,
    create_next_day,
    should_create_new_day,
    is_day_current,
)
from .food_entries import (
    save_food_entries,
    get_food_entries_for_day,
    get_food_entry_by_id,
    update_food_entry,
    delete_food_entries,
    count_food_entries_for_day,
    get_day_totals,
)

# Инициализация базы данных при импорте
init_database()

__all__ = [
    'get_connection',
    'init_database',
    'save_user',
    'get_user_timezone',
    'set_user_timezone',
    'get_or_create_current_day',
    'create_next_day',
    'should_create_new_day',
    'is_day_current',
    'save_food_entries',
    'get_food_entries_for_day',
    'get_food_entry_by_id',
    'update_food_entry',
    'delete_food_entries',
    'count_food_entries_for_day',
    'get_day_totals',
]
