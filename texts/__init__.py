"""
Модуль с текстовыми сообщениями бота.
Импорты для обратной совместимости.
"""

from .telegram_texts import (
    get_start_text,
    HELP_TEXT,
    get_processing_text,
    get_food_entries_saved_text,
    AI_ERROR_TEXT,
    get_nextday_success_text,
    NEXTDAY_ERROR_TEXT,
    get_dayresult_no_entries_text,
    DAYRESULT_ERROR_TEXT,
    get_dayresult_text,
    DATABASE_ERROR_TEXT,
)

from .terminal_texts import (
    TOKEN_ERROR_TEXT,
    BOT_START_HEADER,
    BOT_START_TITLE,
    BOT_START_FOOTER,
    get_token_loaded_text,
    BOT_STARTED_TEXT,
    BOT_ERROR_TEXT,
)
