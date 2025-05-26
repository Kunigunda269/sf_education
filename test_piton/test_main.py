import unittest
from unittest.mock import patch, MagicMock
import datetime
from main import (
    get_current_time, 
    should_use_tool, 
    process_message, 
    Config,
    TimeResponse,
    Message,
    State,
    validate_api_key,
    call_tool,
    call_llm
)

class TestMain(unittest.TestCase):
    def setUp(self):
        """Подготовка тестового окружения."""
        self.valid_state: State = {
            "messages": [{"role": "user", "content": "What time is it?"}]
        }
        self.empty_state: State = {"messages": []}
        self.invalid_state: State = {"messages": None}

    def test_get_current_time(self):
        """Тест функции получения текущего времени."""
        # Проверка структуры ответа
        result = get_current_time()
        self.assertIsInstance(result, dict)
        self.assertIn('utc', result)
        self.assertTrue(isinstance(result['utc'], str))
        self.assertTrue(result['utc'].endswith('Z'))

        # Проверка формата времени
        time_str = result['utc']
        try:
            datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except ValueError:
            self.fail("Time string is not in valid ISO format")

    def test_validate_api_key(self):
        """Тест валидации API ключа."""
        # Тест с отсутствующим ключом
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                validate_api_key()

        # Тест с валидным ключом
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            try:
                validate_api_key()
            except ValueError:
                self.fail("validate_api_key raised ValueError unexpectedly!")

    def test_should_use_tool(self):
        """Тест определения необходимости использования инструмента."""
        # Тест с запросом о времени
        self.assertTrue(should_use_tool(self.valid_state))

        # Тест с обычным сообщением
        state = {
            "messages": [{"role": "user", "content": "Hello"}]
        }
        self.assertFalse(should_use_tool(state))

        # Тест с пустым состоянием
        self.assertFalse(should_use_tool(self.empty_state))

        # Тест с невалидным состоянием
        self.assertFalse(should_use_tool(self.invalid_state))

        # Тест с разными вариантами запроса о времени
        time_queries = [
            "what time is it",
            "tell me the time",
            "current time",
            "time now",
            "what's the time"
        ]
        for query in time_queries:
            state = {
                "messages": [{"role": "user", "content": query}]
            }
            self.assertTrue(should_use_tool(state))

    @patch('main.client')
    def test_call_llm(self, mock_client):
        """Тест вызова LLM."""
        # Настройка мока
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response

        # Тест успешного вызова
        result = call_llm(self.valid_state)
        self.assertIn("messages", result)
        self.assertEqual(len(result["messages"]), 2)
        self.assertEqual(result["messages"][-1]["content"], "Test response")

        # Тест с пустым ответом
        mock_response.choices = []
        with self.assertRaises(ValueError):
            call_llm(self.valid_state)

        # Тест с ошибкой API
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        result = call_llm(self.valid_state)
        self.assertIn("Sorry, I encountered an error", result["messages"][-1]["content"])

    def test_call_tool(self):
        """Тест вызова инструмента."""
        # Тест успешного вызова
        result = call_tool(self.valid_state)
        self.assertIn("messages", result)
        self.assertEqual(len(result["messages"]), 2)
        self.assertIn("Current UTC time is:", result["messages"][-1]["content"])

        # Тест с ошибкой
        with patch('main.tool_executor.execute', side_effect=Exception("Tool Error")):
            result = call_tool(self.valid_state)
            self.assertIn("Sorry, I couldn't get the current time", result["messages"][-1]["content"])

    @patch('main.client')
    def test_process_message(self, mock_client):
        """Тест обработки сообщений."""
        # Настройка мока
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response

        # Тест обработки обычного сообщения
        result = process_message("Hello")
        self.assertEqual(result, "Test response")

        # Тест обработки пустого сообщения
        result = process_message("")
        self.assertEqual(result, "Please enter a valid message.")

        # Тест обработки сообщения с пробелами
        result = process_message("   ")
        self.assertEqual(result, "Please enter a valid message.")

        # Тест обработки None
        result = process_message(None)
        self.assertEqual(result, "Please enter a valid message.")

    def test_config(self):
        """Тест конфигурации."""
        self.assertEqual(Config.MODEL, "gpt-3.5-turbo")
        self.assertEqual(Config.TEMPERATURE, 0)
        self.assertEqual(Config.MAX_RETRIES, 3)
        self.assertEqual(Config.RETRY_DELAY, 1)
        self.assertEqual(Config.TIMEOUT, 30)

if __name__ == '__main__':
    unittest.main() 