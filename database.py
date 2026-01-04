import sqlite3
from datetime import datetime
import os

# Путь к файлу базы данных
DB_PATH = "kbju_bot.db"

def init_database():
    """Инициализация базы данных: создание таблиц"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица дней
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_number INTEGER DEFAULT 1,
                is_current BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, day_number)
            )
        ''')
        
        # Таблица записей о еде (ОБНОВЛЕНА - теперь храним реальные значения)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS food_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_id INTEGER,
                dish_name TEXT NOT NULL,
                calories INTEGER DEFAULT 400,
                protein INTEGER DEFAULT 10,
                fat INTEGER DEFAULT 10,
                carbs INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (day_id) REFERENCES days (id)
            )
        ''')
        
        # Индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_day ON food_entries(user_id, day_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_day ON food_entries(day_id)')
        
        conn.commit()
        print(f"✅ База данных инициализирована: {DB_PATH}")
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при создании базы данных: {e}")
    finally:
        if conn:
            conn.close()

def save_user(user_id, username, first_name, last_name):
    """Сохранение информации о пользователе"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            
            # Создаем первый день для пользователя
            cursor.execute('''
                INSERT INTO days (user_id, day_number, is_current)
                VALUES (?, 1, 1)
            ''', (user_id,))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Ошибка при сохранении пользователя: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_or_create_current_day(user_id):
    """Получает текущий день пользователя, создает если нет"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, day_number FROM days 
            WHERE user_id = ? AND is_current = 1
        ''', (user_id,))
        
        day = cursor.fetchone()
        
        if not day:
            cursor.execute('''
                INSERT INTO days (user_id, day_number, is_current)
                VALUES (?, 1, 1)
            ''', (user_id,))
            day_id = cursor.lastrowid
            day_number = 1
        else:
            day_id, day_number = day
        
        conn.commit()
        return day_id, day_number
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении текущего дня: {e}")
        return None, None
    finally:
        if conn:
            conn.close()

def create_next_day(user_id):
    """Создает следующий день для пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

def save_food_entries(user_id, day_id, dishes):
    """Сохраняет несколько записей о еде за один раз"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

def get_food_entries_for_day(user_id, day_id):
    """Получение записей о еде за день"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

def get_day_totals(user_id, day_id):
    """Получение суммарных КБЖУ за день"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

# Для обратной совместимости
def save_message(user_id, message_text):
    """Совместимость со старой версией"""
    day_id, _ = get_or_create_current_day(user_id)
    if day_id:
        dishes = [{'name': message_text, 'calories': 400, 'protein': 10, 'fat': 10, 'carbs': 10}]
        save_food_entries(user_id, day_id, dishes)
        return True
    return False

init_database()