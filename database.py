import sqlite3
from datetime import datetime, timedelta
import pytz

# Путь к файлу базы данных
DB_PATH = "kbju_bot.db"

# Время автоматического перехода на следующий день (4:00 утра)
AUTO_NEXT_DAY_HOUR = 4

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

def get_user_timezone(user_id):
    """Получает часовой пояс пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

def set_user_timezone(user_id, timezone):
    """Устанавливает часовой пояс пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

def should_create_new_day(user_id, day_created_at):
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

def get_or_create_current_day(user_id):
    """Получает текущий день пользователя, создает если нет или если прошло 4:00 в часовом поясе пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

def count_food_entries_for_day(user_id, day_id):
    """Подсчет количества записей о еде за день"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

init_database()