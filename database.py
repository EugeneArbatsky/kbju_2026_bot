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
        
        # Таблица сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица для продуктов (для будущего расширения)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                calories REAL DEFAULT 0,
                protein REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                carbs REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
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
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Ошибка при сохранении пользователя: {e}")
        return False
    finally:
        if conn:
            conn.close()

def save_message(user_id, message_text):
    """Сохранение сообщения пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (user_id, message_text)
            VALUES (?, ?)
        ''', (user_id, message_text))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Ошибка при сохранении сообщения: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_user_messages(user_id, limit=10):
    """Получение последних сообщений пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message_text, created_at 
            FROM messages 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        messages = cursor.fetchall()
        return messages
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении сообщений: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_message_stats(user_id):
    """Получение статистики по сообщениям"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Общее количество сообщений
        cursor.execute('SELECT COUNT(*) FROM messages WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()[0]
        
        # Дата первого сообщения
        cursor.execute('SELECT MIN(created_at) FROM messages WHERE user_id = ?', (user_id,))
        first_date = cursor.fetchone()[0]
        
        # Дата последнего сообщения
        cursor.execute('SELECT MAX(created_at) FROM messages WHERE user_id = ?', (user_id,))
        last_date = cursor.fetchone()[0]
        
        return {
            'total_messages': total,
            'first_message': first_date,
            'last_message': last_date
        }
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении статистики: {e}")
        return {}
    finally:
        if conn:
            conn.close()

# Автоматически инициализируем базу данных при импорте
init_database()

# Тест базы данных (запустится только если запустить этот файл напрямую)
if __name__ == "__main__":
    print("🧪 Тестирование базы данных...")
    init_database()
    
    # Тестовый пользователь
    save_user(123456, "test_user", "Иван", "Иванов")
    
    # Тестовые сообщения
    save_message(123456, "Привет, бот!")
    save_message(123456, "Как дела?")
    save_message(123456, "Хочу добавить продукт")
    
    # Получаем сообщения
    messages = get_user_messages(123456)
    print("📨 Сообщения тестового пользователя:")
    for msg in messages:
        print(f"  - {msg[1]}: {msg[0]}")
    
    # Получаем статистику
    stats = get_message_stats(123456)
    print(f"📊 Статистика: {stats['total_messages']} сообщений")
    
    print("✅ Тест базы данных завершён успешно!")