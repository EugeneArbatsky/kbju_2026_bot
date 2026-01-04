import sqlite3
from datetime import datetime, date
import os

# Путь к файлу базы данных
DB_PATH = "kbju_bot.db"

def init_database():
    """Инициализация базы данных: создание таблиц"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Таблица пользователей (оставляем как есть)
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
        
        # Таблица записей о еде (вместо messages)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS food_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_id INTEGER,
                message_text TEXT,
                calories REAL DEFAULT 400,
                protein REAL DEFAULT 10,
                fat REAL DEFAULT 10,
                carbs REAL DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (day_id) REFERENCES days (id)
            )
        ''')
        
        # Старая таблица messages (оставим для обратной совместимости)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            # Добавляем нового пользователя
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
        
        # Ищем текущий день
        cursor.execute('''
            SELECT id, day_number FROM days 
            WHERE user_id = ? AND is_current = 1
        ''', (user_id,))
        
        day = cursor.fetchone()
        
        if not day:
            # Если нет текущего дня, создаем первый
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
        
        # Получаем текущий день
        cursor.execute('''
            SELECT id, day_number FROM days 
            WHERE user_id = ? AND is_current = 1
        ''', (user_id,))
        
        current_day = cursor.fetchone()
        
        if not current_day:
            # Если нет дней, создаем первый
            cursor.execute('''
                INSERT INTO days (user_id, day_number, is_current)
                VALUES (?, 1, 1)
            ''', (user_id,))
            day_id = cursor.lastrowid
            day_number = 1
        else:
            current_day_id, current_day_number = current_day
            
            # Снимаем флаг текущего дня с предыдущего
            cursor.execute('''
                UPDATE days SET is_current = 0 
                WHERE id = ?
            ''', (current_day_id,))
            
            # Создаем новый день
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

def save_food_entry(user_id, day_id, message_text):
    """Сохранение записи о еде"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO food_entries (user_id, day_id, message_text)
            VALUES (?, ?, ?)
        ''', (user_id, day_id, message_text))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Ошибка при сохранении записи о еде: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_food_entries_for_day(user_id, day_id):
    """Получение записей о еде за день"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, message_text, calories, protein, fat, carbs
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

# Для обратной совместимости оставим старые функции
def save_message(user_id, message_text):
    return save_food_entry(user_id, 1, message_text)  # Просто для совместимости

def get_user_messages(user_id, limit=10):
    """Получение последних сообщений пользователя (для обратной совместимости)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message_text, created_at 
            FROM food_entries 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        messages = cursor.fetchall()
        return messages
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении сообщений: {e}")
        return []

def get_message_stats(user_id):
    """Получение статистики по сообщениям"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM food_entries WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(created_at) FROM food_entries WHERE user_id = ?', (user_id,))
        first_date = cursor.fetchone()[0]
        
        cursor.execute('SELECT MAX(created_at) FROM food_entries WHERE user_id = ?', (user_id,))
        last_date = cursor.fetchone()[0]
        
        return {
            'total_messages': total,
            'first_message': first_date,
            'last_message': last_date
        }
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении статистики: {e}")
        return {}

# Автоматически инициализируем базу данных при импорте
init_database()