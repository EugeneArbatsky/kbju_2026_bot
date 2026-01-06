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
    get_timezone_info_text,
    get_timezone_set_text,
    TIMEZONE_INVALID_TEXT,
    TIMEZONE_ERROR_TEXT,
    DATABASE_ERROR_TEXT,
    EDIT_PROMPT_TEXT,
    EDIT_SUCCESS_TEXT,
    EDIT_CANCEL_TEXT,
    EDIT_ERROR_TEXT,
    EDIT_NOT_CURRENT_DAY_TEXT,
    EDIT_NOT_FOUND_TEXT,
    EDIT_UPDATED_SUFFIX,
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
