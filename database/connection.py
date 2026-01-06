"""
Управление подключением к базе данных.
"""

import sqlite3
from typing import Optional

# Путь к файлу базы данных
DB_PATH = "kbju_bot.db"


def get_connection() -> sqlite3.Connection:
    """
    Получает подключение к базе данных.
    
    Returns:
        Подключение к SQLite базе данных
    """
    return sqlite3.connect(DB_PATH)


def init_database():
    """Инициализация базы данных: создание таблиц"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                timezone TEXT DEFAULT 'Europe/Moscow',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Миграция: добавляем поле timezone если его нет
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT "Europe/Moscow"')
        except sqlite3.OperationalError:
            # Поле уже существует, игнорируем ошибку
            pass
        
        # Обновляем существующих пользователей без часового пояса на Москву
        cursor.execute('''
            UPDATE users SET timezone = 'Europe/Moscow' 
            WHERE timezone IS NULL OR timezone = 'UTC'
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
        
        # Таблица записей о еде
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
