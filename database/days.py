"""
Работа с днями в базе данных.
"""

import sqlite3
from datetime import datetime, timedelta
import pytz
from typing import Optional, Tuple
from .connection import get_connection
from .users import get_user_timezone

# Время автоматического перехода на следующий день (4:00 утра)
AUTO_NEXT_DAY_HOUR = 4


def _create_first_day(cursor: sqlite3.Cursor, user_id: int) -> None:
    """Вспомогательная функция для создания первого дня пользователя"""
    cursor.execute('''
        INSERT INTO days (user_id, day_number, is_current)
        VALUES (?, 1, 1)
    ''', (user_id,))


def should_create_new_day(user_id: int, day_created_at) -> bool:
    """Проверяет, нужно ли создавать новый день на основе времени 4:00 в часовом поясе пользователя"""
    try:
        timezone_str = get_user_timezone(user_id)
        
        # Получаем часовой пояс пользователя
        try:
            user_tz = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            # Если часовой пояс неизвестен, используем UTC
            user_tz = pytz.UTC
        
        # Текущее время в часовом поясе пользователя
        now_user = datetime.now(user_tz)
        
        # Время создания дня в часовом поясе пользователя
        # day_created_at хранится в UTC, конвертируем в часовой пояс пользователя
        utc_tz = pytz.UTC
        # Парсим timestamp из базы данных
        if isinstance(day_created_at, str):
            # Пробуем разные форматы
            try:
                day_created_utc = datetime.fromisoformat(day_created_at.replace('Z', '+00:00'))
            except ValueError:
                try:
                    day_created_utc = datetime.strptime(day_created_at, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    day_created_utc = datetime.strptime(day_created_at, '%Y-%m-%d %H:%M:%S.%f')
        else:
            day_created_utc = datetime.fromtimestamp(day_created_at)
        
        if day_created_utc.tzinfo is None:
            day_created_utc = utc_tz.localize(day_created_utc)
        day_created_user = day_created_utc.astimezone(user_tz)
        
        # Вычисляем дату "начала дня" для дня создания (4:00 утра того дня)
        day_start_created = day_created_user.replace(hour=AUTO_NEXT_DAY_HOUR, minute=0, second=0, microsecond=0)
        if day_created_user.hour < AUTO_NEXT_DAY_HOUR:
            # День был создан до 4:00, значит начало дня - это 4:00 предыдущего дня
            day_start_created = day_start_created - timedelta(days=1)
        
        # Вычисляем дату "начала дня" для текущего момента (4:00 утра сегодня)
        day_start_now = now_user.replace(hour=AUTO_NEXT_DAY_HOUR, minute=0, second=0, microsecond=0)
        if now_user.hour < AUTO_NEXT_DAY_HOUR:
            # Сейчас до 4:00, значит начало дня - это 4:00 вчера
            day_start_now = day_start_now - timedelta(days=1)
        
        # Если начало текущего дня > начала дня создания, значит нужно создать новый день
        return day_start_now > day_start_created
        
    except Exception as e:
        print(f"❌ Ошибка при проверке необходимости нового дня: {e}")
        return False


def get_or_create_current_day(user_id: int) -> Tuple[Optional[int], Optional[int]]:
    """Получает текущий день пользователя, создает если нет или если прошло 4:00 в часовом поясе пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, day_number, created_at FROM days 
            WHERE user_id = ? AND is_current = 1
        ''', (user_id,))
        
        day = cursor.fetchone()
        
        if not day:
            # Дня нет, создаем первый
            cursor.execute('''
                INSERT INTO days (user_id, day_number, is_current)
                VALUES (?, 1, 1)
            ''', (user_id,))
            day_id = cursor.lastrowid
            day_number = 1
        else:
            day_id, day_number, day_created_at = day
            
            # Проверяем, нужно ли автоматически создать новый день
            if should_create_new_day(user_id, day_created_at):
                # Создаем новый день автоматически
                cursor.execute('''
                    UPDATE days SET is_current = 0 
                    WHERE id = ?
                ''', (day_id,))
                
                new_day_number = day_number + 1
                cursor.execute('''
                    INSERT INTO days (user_id, day_number, is_current)
                    VALUES (?, ?, 1)
                ''', (user_id, new_day_number))
                
                day_id = cursor.lastrowid
                day_number = new_day_number
                print(f"🌅 Автоматически создан новый день {day_number} для пользователя {user_id}")
        
        conn.commit()
        return day_id, day_number
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении текущего дня: {e}")
        return None, None
    finally:
        if conn:
            conn.close()


def create_next_day(user_id: int) -> Tuple[Optional[int], Optional[int]]:
    """Создает следующий день для пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, day_number FROM days 
            WHERE user_id = ? AND is_current = 1
        ''', (user_id,))
        
        current_day = cursor.fetchone()
        
        if not current_day:
            cursor.execute('''
                INSERT INTO days (user_id, day_number, is_current)
                VALUES (?, 1, 1)
            ''', (user_id,))
            day_id = cursor.lastrowid
            day_number = 1
        else:
            current_day_id, current_day_number = current_day
            
            cursor.execute('''
                UPDATE days SET is_current = 0 
                WHERE id = ?
            ''', (current_day_id,))
            
            new_day_number = current_day_number + 1
            cursor.execute('''
                INSERT INTO days (user_id, day_number, is_current)
                VALUES (?, ?, 1)
            ''', (user_id, new_day_number))
            
            day_id = cursor.lastrowid
            day_number = new_day_number
        
        conn.commit()
        return day_id, day_number
    except sqlite3.Error as e:
        print(f"❌ Ошибка при создании следующего дня: {e}")
        return None, None
    finally:
        if conn:
            conn.close()


def is_day_current(user_id: int, day_id: int) -> bool:
    """Проверяет, является ли день текущим для пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT is_current FROM days 
            WHERE id = ? AND user_id = ?
        ''', (day_id, user_id))
        
        result = cursor.fetchone()
        return result and result[0] == 1
    except sqlite3.Error as e:
        print(f"❌ Ошибка при проверке текущего дня: {e}")
        return False
    finally:
        if conn:
            conn.close()
