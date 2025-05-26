import datetime
import os
import logging
import time
import asyncio
from typing import Dict, List, Tuple, Any, Optional, TypedDict, Callable
from dataclasses import dataclass
from functools import wraps
from dotenv import load_dotenv
from langgraph.graph import Graph
from langgraph.prebuilt import ToolExecutor
from langgraph.prebuilt.tool_executor import Tool
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.error import APIError, RateLimitError, Timeout
import aiohttp
from aiohttp import ClientSession, ClientTimeout

from utils import (
    clean_message,
    is_time_query,
    format_error_message,
    check_rate_limit,
    validate_token_count,
    get_cached_time,
    validate_api_key_format
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
@dataclass
class Config:
    MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1
    TIMEOUT: int = 30
    MAX_TOKENS: int = 1000
    CACHE_SIZE: int = 100
    HTTP_TIMEOUT: int = 30
    MAX_CONNECTIONS: int = 100
    HEALTH_CHECK_INTERVAL: int = 60

# Типы
class TimeResponse(TypedDict):
    utc: str

class Message(TypedDict):
    role: str
    content: str

class State(TypedDict):
    messages: List[Message]

# Мониторинг состояния приложения
class AppMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.last_health_check = time.time()
        self._session: Optional[ClientSession] = None

    @property
    def uptime(self) -> float:
        return time.time() - self.start_time

    @property
    def error_rate(self) -> float:
        return self.error_count / max(self.request_count, 1)

    async def get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=Config.HTTP_TIMEOUT)
            self._session = ClientSession(
                timeout=timeout,
                connector=aiohttp.TCPConnector(
                    limit=Config.MAX_CONNECTIONS,
                    ttl_dns_cache=300
                )
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def increment_requests(self):
        self.request_count += 1

    def increment_errors(self):
        self.error_count += 1

    def should_check_health(self) -> bool:
        return time.time() - self.last_health_check > Config.HEALTH_CHECK_INTERVAL

    def update_health_check(self):
        self.last_health_check = time.time()

# Создаем экземпляр монитора
monitor = AppMonitor()

# Декоратор для повторных попыток
def retry_on_error(max_retries: int = Config.MAX_RETRIES, 
                  delay: int = Config.RETRY_DELAY,
                  exceptions: Tuple[Exception, ...] = (APIError, RateLimitError, Timeout)):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    monitor.increment_errors()
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Экспоненциальная задержка
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
            logger.error(f"All {max_retries} attempts failed. Last error: {str(last_exception)}")
            raise last_exception
        return wrapper
    return decorator

# Загрузка переменных окружения
def load_env():
    """Загружает переменные окружения с обработкой ошибок."""
    try:
        if not os.path.exists('.env'):
            logger.warning(".env file not found, using environment variables")
        load_dotenv()
    except Exception as e:
        logger.error(f"Error loading environment variables: {e}")
        raise

def get_current_time() -> TimeResponse:
    """Return the current UTC time in ISO‑8601 format."""
    try:
        current_time = get_cached_time()
        logger.info(f"Generated current time: {current_time}")
        return {"utc": current_time}
    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        monitor.increment_errors()
        raise

def validate_api_key() -> None:
    """Проверяет наличие и валидность API ключа."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    if not validate_api_key_format(api_key):
        raise ValueError("Invalid API key format")
    logger.info("API key validation successful")

# Создаем инструмент для получения времени
tools = [
    Tool(
        name="get_current_time",
        description="Get the current UTC time in ISO-8601 format",
        func=get_current_time
    )
]

# Создаем исполнитель инструментов
tool_executor = ToolExecutor(tools)

# Инициализация клиента OpenAI
async def init_openai_client() -> OpenAI:
    """Инициализирует клиент OpenAI с обработкой ошибок."""
    try:
        validate_api_key()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("OpenAI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        monitor.increment_errors()
        raise

# Инициализация клиента
client = None

def should_use_tool(state: State) -> bool:
    """Определяет, нужно ли использовать инструмент."""
    try:
        if "messages" not in state:
            logger.error("State missing 'messages' key")
            return False
            
        messages = state["messages"]
        if not messages:
            return False
            
        last_message = messages[-1]["content"].lower()
        should_use = is_time_query(last_message)
        logger.info(f"Should use tool: {should_use} for message: {last_message}")
        return should_use
    except Exception as e:
        logger.error(f"Error in should_use_tool: {e}")
        monitor.increment_errors()
        return False

def call_tool(state: State) -> State:
    """Вызывает инструмент get_current_time."""
    try:
        result = tool_executor.execute("get_current_time", {})
        response = f"Current UTC time is: {result['utc']}"
        state["messages"].append({
            "role": "assistant",
            "content": response
        })
        logger.info(f"Tool called successfully: {response}")
        return state
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        monitor.increment_errors()
        state["messages"].append({
            "role": "assistant",
            "content": format_error_message(e)
        })
        return state

@retry_on_error()
async def call_llm(state: State) -> State:
    """Вызывает LLM для генерации ответа."""
    try:
        global client
        if client is None:
            client = await init_openai_client()

        # Проверка rate limit
        allowed, error_message = check_rate_limit()
        if not allowed:
            raise RateLimitError(error_message)

        messages = state["messages"]
        
        # Проверка количества токенов
        total_tokens = sum(estimate_tokens(m["content"]) for m in messages)
        if total_tokens > Config.MAX_TOKENS:
            raise ValueError(f"Message too long. Maximum {Config.MAX_TOKENS} tokens allowed.")
        
        response: ChatCompletion = await client.chat.completions.create(
            model=Config.MODEL,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=Config.TEMPERATURE,
            timeout=Config.TIMEOUT,
            max_tokens=Config.MAX_TOKENS
        )
        
        if not response.choices:
            raise ValueError("Empty response from LLM")
            
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty content in LLM response")
            
        state["messages"].append({
            "role": "assistant",
            "content": content
        })
        logger.info(f"LLM response generated: {content[:50]}...")
        return state
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        monitor.increment_errors()
        state["messages"].append({
            "role": "assistant",
            "content": format_error_message(e)
        })
        return state

# Создаем граф
workflow = Graph()

# Добавляем узлы
workflow.add_node("should_use_tool", should_use_tool)
workflow.add_node("call_tool", call_tool)
workflow.add_node("call_llm", call_llm)

# Добавляем ребра
workflow.add_edge("should_use_tool", "call_tool", condition=lambda x: x["should_use_tool"])
workflow.add_edge("should_use_tool", "call_llm", condition=lambda x: not x["should_use_tool"])

# Компилируем граф
app = workflow.compile()

async def process_message_async(message: str) -> str:
    """Асинхронная обработка сообщения пользователя."""
    try:
        monitor.increment_requests()
        
        # Очистка и валидация сообщения
        cleaned_message = clean_message(message)
        if not cleaned_message:
            return "Please enter a valid message."
        
        state: State = {
            "messages": [{"role": "user", "content": cleaned_message}]
        }
        
        # Проверка количества токенов
        if not validate_token_count(cleaned_message):
            return f"Message too long. Maximum {Config.MAX_TOKENS} tokens allowed."
        
        result = await asyncio.to_thread(app.invoke, state)
        return result["messages"][-1]["content"]
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        monitor.increment_errors()
        return format_error_message(e)

def process_message(message: str) -> str:
    """Обрабатывает сообщение пользователя."""
    return asyncio.run(process_message_async(message))

async def main():
    """Основная функция приложения."""
    logger.info("Starting chat application")
    try:
        load_env()
        await init_openai_client()
        
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                logger.info("User requested exit")
                break
            response = await process_message_async(user_input)
            print(f"Assistant: {response}")
            
            # Проверка состояния приложения
            if monitor.should_check_health():
                logger.info(f"Application health: uptime={monitor.uptime:.2f}s, "
                          f"requests={monitor.request_count}, "
                          f"error_rate={monitor.error_rate:.2%}")
                monitor.update_health_check()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await monitor.close()
        logger.info("Application stopped")

if __name__ == "__main__":
    asyncio.run(main()) 