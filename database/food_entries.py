"""
Работа с записями о еде в базе данных.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from .connection import get_connection


def save_food_entries(user_id: int, day_id: int, dishes: List[Dict[str, Any]]) -> List[int]:
    """Сохраняет несколько записей о еде за один раз"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        saved_ids = []
        for dish in dishes:
            cursor.execute('''
                INSERT INTO food_entries 
                (user_id, day_id, dish_name, calories, protein, fat, carbs)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, day_id, 
                dish['name'], dish['calories'], 
                dish['protein'], dish['fat'], dish['carbs']
            ))
            saved_ids.append(cursor.lastrowid)
        
        conn.commit()
        return saved_ids
    except sqlite3.Error as e:
        print(f"❌ Ошибка при сохранении записей о еде: {e}")
        return []
    finally:
        if conn:
            conn.close()


def count_food_entries_for_day(user_id: int, day_id: int) -> int:
    """Подсчет количества записей о еде за день"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM food_entries 
            WHERE user_id = ? AND day_id = ?
        ''', (user_id, day_id))
        
        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error as e:
        print(f"❌ Ошибка при подсчете записей о еде: {e}")
        return 0
    finally:
        if conn:
            conn.close()


def get_food_entries_for_day(user_id: int, day_id: int) -> List[tuple]:
    """Получение записей о еде за день"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, dish_name, calories, protein, fat, carbs
            FROM food_entries 
            WHERE user_id = ? AND day_id = ?
            ORDER BY created_at
        ''', (user_id, day_id))
        
        entries = cursor.fetchall()
        return entries
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении записей о еде: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_day_totals(user_id: int, day_id: int) -> Dict[str, Any]:
    """Получение суммарных КБЖУ за день"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                SUM(calories) as total_calories,
                SUM(protein) as total_protein,
                SUM(fat) as total_fat,
                SUM(carbs) as total_carbs,
                COUNT(*) as count
            FROM food_entries 
            WHERE user_id = ? AND day_id = ?
        ''', (user_id, day_id))
        
        result = cursor.fetchone()
        if result and result[0] is not None:
            return {
                'calories': round(result[0]),
                'protein': round(result[1]),
                'fat': round(result[2]),
                'carbs': round(result[3]),
                'count': result[4]
            }
        else:
            return {
                'calories': 0,
                'protein': 0,
                'fat': 0,
                'carbs': 0,
                'count': 0
            }
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении суммарных КБЖУ: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def get_food_entry_by_id(entry_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Получение записи о еде по ID с проверкой пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, day_id, dish_name, calories, protein, fat, carbs
            FROM food_entries 
            WHERE id = ? AND user_id = ?
        ''', (entry_id, user_id))
        
        entry = cursor.fetchone()
        if entry:
            return {
                'id': entry[0],
                'user_id': entry[1],
                'day_id': entry[2],
                'name': entry[3],
                'calories': entry[4],
                'protein': entry[5],
                'fat': entry[6],
                'carbs': entry[7]
            }
        return None
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении записи о еде: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_food_entry(
    entry_id: int,
    user_id: int,
    dish_name: str,
    calories: int,
    protein: int,
    fat: int,
    carbs: int
) -> bool:
    """Обновление записи о еде"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE food_entries 
            SET dish_name = ?, calories = ?, protein = ?, fat = ?, carbs = ?
            WHERE id = ? AND user_id = ?
        ''', (dish_name, calories, protein, fat, carbs, entry_id, user_id))
        
        if cursor.rowcount == 0:
            return False
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Ошибка при обновлении записи о еде: {e}")
        return False
    finally:
        if conn:
            conn.close()


def delete_food_entries(entry_ids: List[int], user_id: int) -> bool:
    """Удаляет записи о еде по списку ID с проверкой пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, что все записи принадлежат пользователю
        placeholders = ','.join('?' * len(entry_ids))
        cursor.execute(f'''
            SELECT COUNT(*) FROM food_entries 
            WHERE id IN ({placeholders}) AND user_id = ?
        ''', (*entry_ids, user_id))
        
        count = cursor.fetchone()[0]
        if count != len(entry_ids):
            print(f"⚠️  Не все записи найдены или принадлежат пользователю {user_id}")
            return False
        
        # Удаляем записи
        cursor.execute(f'''
            DELETE FROM food_entries 
            WHERE id IN ({placeholders}) AND user_id = ?
        ''', (*entry_ids, user_id))
        
        conn.commit()
        deleted_count = cursor.rowcount
        
        if deleted_count == len(entry_ids):
            print(f"✅ Удалено {deleted_count} записей о еде")
            return True
        else:
            print(f"⚠️  Удалено {deleted_count} из {len(entry_ids)} записей")
            return False
    except sqlite3.Error as e:
        print(f"❌ Ошибка при удалении записей о еде: {e}")
        return False
    finally:
        if conn:
            conn.close()
