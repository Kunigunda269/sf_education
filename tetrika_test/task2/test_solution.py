import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import csv
import io
from solution import get_animals_from_wikipedia, save_to_csv, main


class TestWikipediaParser(unittest.TestCase):
    
    def test_save_to_csv(self):
        """Тест сохранения данных в CSV файл"""
        # Тестовые данные
        test_data = {
            'А': 5,
            'Б': 0,  # Эта буква не должна попасть в файл
            'В': 3,
            'Г': 1
        }
        
        # Мокируем открытие файла
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            save_to_csv(test_data)
        
        # Проверяем вызовы
        mock_file.assert_called_once_with('beasts.csv', 'w', newline='', encoding='utf-8')
        
        # Получаем записанные данные
        written_data = mock_file().write.call_args_list
        written_content = ''.join([call[0][0] for call in written_data])
        
        # Проверяем содержимое
        expected_lines = ['А,5', 'В,3', 'Г,1']
        for line in expected_lines:
            self.assertIn(line, written_content)
        
        # Проверяем, что буква Б с нулевым счетчиком не записана
        self.assertNotIn('Б,0', written_content)
    
    @patch('requests.get')
    def test_get_animals_from_wikipedia_single_page(self, mock_get):
        """Тест получения данных с одной страницы API"""
        # Мокируем ответ API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'query': {
                'categorymembers': [
                    {'title': 'Аист'},
                    {'title': 'Акула'},
                    {'title': 'Бегемот'},
                    {'title': 'Волк'},
                    {'title': 'Ворона'},
                    {'title': 'Ворона серая'}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Вызываем функцию
        result = get_animals_from_wikipedia()
        
        # Проверяем результаты
        self.assertEqual(result['А'], 2)  # Аист, Акула
        self.assertEqual(result['Б'], 1)  # Бегемот
        self.assertEqual(result['В'], 3)  # Волк, Ворона, Ворона серая
        self.assertEqual(result['Г'], 0)  # Нет животных на Г
    
    @patch('requests.get')
    def test_get_animals_from_wikipedia_multiple_pages(self, mock_get):
        """Тест получения данных с нескольких страниц API"""
        # Первый ответ с токеном продолжения
        first_response = MagicMock()
        first_response.json.return_value = {
            'query': {
                'categorymembers': [
                    {'title': 'Аист'},
                    {'title': 'Бегемот'}
                ]
            },
            'continue': {
                'cmcontinue': 'page2token'
            }
        }
        first_response.raise_for_status.return_value = None
        
        # Второй ответ без токена продолжения
        second_response = MagicMock()
        second_response.json.return_value = {
            'query': {
                'categorymembers': [
                    {'title': 'Волк'},
                    {'title': 'Гепард'}
                ]
            }
        }
        second_response.raise_for_status.return_value = None
        
        # Настраиваем мок для возврата разных ответов
        mock_get.side_effect = [first_response, second_response]
        
        # Вызываем функцию
        result = get_animals_from_wikipedia()
        
        # Проверяем, что API вызывался дважды
        self.assertEqual(mock_get.call_count, 2)
        
        # Проверяем результаты
        self.assertEqual(result['А'], 1)  # Аист
        self.assertEqual(result['Б'], 1)  # Бегемот
        self.assertEqual(result['В'], 1)  # Волк
        self.assertEqual(result['Г'], 1)  # Гепард
    
    @patch('requests.get')
    def test_get_animals_from_wikipedia_with_non_russian_letters(self, mock_get):
        """Тест обработки названий, начинающихся не с русских букв"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'query': {
                'categorymembers': [
                    {'title': 'Аист'},
                    {'title': 'Cat'},  # Английская буква - должна игнорироваться
                    {'title': '123 вид'},  # Цифра - должна игнорироваться
                    {'title': 'Бегемот'},
                    {'title': ''},  # Пустое название - должно игнорироваться
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = get_animals_from_wikipedia()
        
        # Проверяем, что учитываются только русские названия
        self.assertEqual(result['А'], 1)  # Аист
        self.assertEqual(result['Б'], 1)  # Бегемот
        # Все остальные буквы должны быть 0
        for letter in 'ВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ':
            self.assertEqual(result[letter], 0)
    
    @patch('requests.get')
    def test_get_animals_from_wikipedia_network_error(self, mock_get):
        """Тест обработки сетевых ошибок"""
        import requests
        
        # Мокируем сетевую ошибку
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Вызываем функцию
        result = get_animals_from_wikipedia()
        
        # Проверяем, что возвращается словарь с нулевыми счетчиками
        for letter in 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ':
            self.assertEqual(result[letter], 0)
    
    @patch('requests.get')
    def test_get_animals_from_wikipedia_invalid_response(self, mock_get):
        """Тест обработки некорректного ответа API"""
        # Мокируем некорректный ответ
        mock_response = MagicMock()
        mock_response.json.return_value = {'error': 'Invalid request'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Вызываем функцию
        result = get_animals_from_wikipedia()
        
        # Проверяем, что возвращается словарь с нулевыми счетчиками
        for letter in 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ':
            self.assertEqual(result[letter], 0)
    
    @patch('solution.save_to_csv')
    @patch('solution.get_animals_from_wikipedia')
    def test_main_function(self, mock_get_animals, mock_save_csv):
        """Тест основной функции"""
        # Мокируем данные
        test_data = {'А': 10, 'Б': 5, 'В': 0}
        mock_get_animals.return_value = test_data
        
        # Перехватываем вывод
        with patch('builtins.print') as mock_print:
            main()
        
        # Проверяем, что функции были вызваны
        mock_get_animals.assert_called_once()
        mock_save_csv.assert_called_once_with(test_data)
        
        # Проверяем, что была попытка вывода результатов
        mock_print.assert_called()


if __name__ == '__main__':
    unittest.main() 