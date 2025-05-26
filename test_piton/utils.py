import re
import html
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
from functools import lru_cache
import time
import tiktoken
import logging

# Константы для обработки сообщений
TIME_QUERIES = [
    "time",
    "what time",
    "current time",
    "tell me the time",
    "what's the time",
    "time now",
    "current time now",
    "what time is it now"
]

# Константы для валидации
MAX_MESSAGE_LENGTH = 1000
MAX_TOKENS = 1000
RATE_LIMIT_WINDOW = 60  # секунды
MAX_REQUESTS_PER_WINDOW = 10
TIME_CACHE_DURATION = 0.1  # секунды
MAX_CACHED_CLIENTS = 1000  # максимальное количество кэшированных клиентов

# Регулярные выражения для валидации
ISO_TIME_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$'
API_KEY_PATTERN = r'^sk-[A-Za-z0-9]{32,}$'
DANGEROUS_PATTERNS = [
    r'<script.*?>',
    r'javascript:',
    r'on\w+\s*=',
    r'data:',
    r'vbscript:',
    r'expression\s*\(',
    r'url\s*\(',
    r'eval\s*\(',
    r'exec\s*\(',
]

# Настройка логирования
logger = logging.getLogger(__name__)

# Кэш для rate limiting с автоматической очисткой
class RateLimitCache:
    def __init__(self, max_size: int = MAX_CACHED_CLIENTS):
        self._cache: Dict[str, list] = {}
        self._max_size = max_size
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 минут

    def _cleanup(self):
        """Очищает старые записи из кэша."""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            # Удаляем старые записи
            for client_id in list(self._cache.keys()):
                self._cache[client_id] = [
                    ts for ts in self._cache[client_id]
                    if current_time - ts < RATE_LIMIT_WINDOW
                ]
                if not self._cache[client_id]:
                    del self._cache[client_id]
            self._last_cleanup = current_time

    def add_request(self, client_id: str) -> bool:
        """Добавляет запрос в кэш и проверяет rate limit."""
        self._cleanup()
        current_time = time.time()

        if client_id not in self._cache:
            if len(self._cache) >= self._max_size:
                # Удаляем самый старый клиент
                oldest_client = min(self._cache.items(), key=lambda x: min(x[1]))[0]
                del self._cache[oldest_client]
            self._cache[client_id] = []

        # Удаляем старые временные метки
        self._cache[client_id] = [
            ts for ts in self._cache[client_id]
            if current_time - ts < RATE_LIMIT_WINDOW
        ]

        if len(self._cache[client_id]) >= MAX_REQUESTS_PER_WINDOW:
            return False

        self._cache[client_id].append(current_time)
        return True

# Создаем экземпляр кэша
rate_limit_cache = RateLimitCache()

def validate_iso_time(time_str: str) -> bool:
    """Проверяет, соответствует ли строка формату ISO-8601."""
    return bool(re.match(ISO_TIME_PATTERN, time_str))

def validate_api_key_format(api_key: str) -> bool:
    """Проверяет формат API ключа."""
    return bool(re.match(API_KEY_PATTERN, api_key))

def clean_message(message: str) -> Optional[str]:
    """
    Очищает и валидирует сообщение пользователя.
    
    Args:
        message: Исходное сообщение
        
    Returns:
        Очищенное сообщение или None, если сообщение невалидно
    """
    if not message or not isinstance(message, str):
        return None
        
    # Удаляем лишние пробелы
    cleaned = message.strip()
    
    # Проверяем длину
    if len(cleaned) > MAX_MESSAGE_LENGTH:
        return None
        
    # Удаляем потенциально опасные символы и паттерны
    cleaned = re.sub(r'[<>]', '', cleaned)
    cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'data:', '', cleaned, flags=re.IGNORECASE)
    
    return cleaned if cleaned else None

def is_time_query(message: str) -> bool:
    """
    Проверяет, является ли сообщение запросом о времени.
    
    Args:
        message: Сообщение пользователя
        
    Returns:
        True, если это запрос о времени
    """
    time_queries = [
        "time",
        "what time",
        "current time",
        "tell me the time",
        "what's the time",
        "который час",
        "сколько времени",
        "текущее время"
    ]
    return any(query in message.lower() for query in time_queries)

def format_error_message(error: Exception) -> str:
    """
    Форматирует сообщение об ошибке для пользователя.
    
    Args:
        error: Объект исключения
        
    Returns:
        Отформатированное сообщение об ошибке
    """
    error_message = str(error)
    # Безопасное логирование ошибки
    logger.error(f"Error occurred: {type(error).__name__}: {error_message}")
    
    if isinstance(error, ValueError):
        return str(error)
    elif isinstance(error, TimeoutError):
        return "Request timed out. Please try again."
    elif isinstance(error, RateLimitError):
        return "Too many requests. Please wait a moment and try again."
    else:
        return "An unexpected error occurred. Please try again."

def check_rate_limit(client_id: str = "default") -> Tuple[bool, str]:
    """
    Проверяет соблюдение rate limit.
    
    Args:
        client_id: Идентификатор клиента
        
    Returns:
        Tuple[bool, str]: (Разрешено ли выполнение, сообщение об ошибке)
    """
    if not rate_limit_cache.add_request(client_id):
        return False, f"Rate limit exceeded. Maximum {MAX_REQUESTS_PER_WINDOW} requests per {RATE_LIMIT_WINDOW} seconds."
    return True, ""

def estimate_tokens(text: str) -> int:
    """
    Оценивает количество токенов в тексте.
    
    Args:
        text: Текст для оценки
        
    Returns:
        Примерное количество токенов
    """
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Failed to estimate tokens using tiktoken: {e}")
        # Если не удалось определить кодировку, используем приблизительную оценку
        return len(text.split()) * 1.3

def validate_token_count(text: str, max_tokens: int = MAX_TOKENS) -> bool:
    """
    Проверяет, не превышает ли текст максимальное количество токенов.
    
    Args:
        text: Текст для проверки
        max_tokens: Максимальное количество токенов
        
    Returns:
        True, если количество токенов в пределах нормы
    """
    return estimate_tokens(text) <= max_tokens

@lru_cache(maxsize=1)
def get_cached_time() -> str:
    """
    Возвращает текущее время в UTC с кэшированием.
    
    Returns:
        Строка с текущим временем в формате ISO-8601
    """
    return datetime.utcnow().isoformat() + 'Z' 