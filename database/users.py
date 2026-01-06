"""
Работа с пользователями в базе данных.
"""

import sqlite3
from typing import Optional
from .connection import get_connection


def save_user(user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> bool:
    """Сохранение информации о пользователе"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            
            # Создаем первый день для пользователя
            from .days import _create_first_day
            _create_first_day(cursor, user_id)
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Ошибка при сохранении пользователя: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_user_timezone(user_id: int) -> str:
    """Получает часовой пояс пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        return 'Europe/Moscow'  # По умолчанию Москва
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении часового пояса: {e}")
        return 'Europe/Moscow'
    finally:
        if conn:
            conn.close()


def set_user_timezone(user_id: int, timezone: str) -> bool:
    """Устанавливает часовой пояс пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            # Создаем пользователя если его нет
            cursor.execute('''
                INSERT INTO users (user_id, timezone)
                VALUES (?, ?)
            ''', (user_id, timezone))
        else:
            cursor.execute('''
                UPDATE users SET timezone = ? WHERE user_id = ?
            ''', (timezone, user_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Ошибка при установке часового пояса: {e}")
        return False
    finally:
        if conn:
            conn.close()
