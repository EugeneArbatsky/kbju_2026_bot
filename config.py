"""
Конфигурация приложения
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# GigaChat API (Authorization Key из кабинета)
GIGACHAT_AUTH_KEY = os.getenv('GIGACHAT_AUTH_KEY')

# Настройки AI
AI_TIMEOUT = 30  # секунд

# Настройки приложения
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Проверка обязательных переменных
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен в .env")

if not GIGACHAT_AUTH_KEY:
    print("⚠️  GIGACHAT_AUTH_KEY не установлен, AI будет работать в режиме заглушки")