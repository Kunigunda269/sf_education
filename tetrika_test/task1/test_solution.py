import unittest
from solution import strict


class TestStrictDecorator(unittest.TestCase):
    
    def test_correct_types(self):
        """Тест корректных типов аргументов"""
        
        @strict
        def sum_two(a: int, b: int) -> int:
            return a + b
        
        @strict
        def concat_strings(s1: str, s2: str) -> str:
            return s1 + s2
        
        @strict
        def multiply_float(a: float, b: float) -> float:
            return a * b
        
        @strict
        def check_bool(flag: bool) -> bool:
            return not flag
        
        # Проверяем корректную работу с правильными типами
        self.assertEqual(sum_two(1, 2), 3)
        self.assertEqual(concat_strings("hello", " world"), "hello world")
        self.assertEqual(multiply_float(2.5, 3.0), 7.5)
        self.assertTrue(check_bool(False))
        self.assertFalse(check_bool(True))
    
    def test_incorrect_types_int(self):
        """Тест некорректных типов для int параметров"""
        
        @strict
        def sum_two(a: int, b: int) -> int:
            return a + b
        
        # Проверяем TypeError для неправильных типов
        with self.assertRaises(TypeError):
            sum_two(1, 2.4)  # float вместо int
        
        with self.assertRaises(TypeError):
            sum_two("1", 2)  # str вместо int
        
        with self.assertRaises(TypeError):
            sum_two(True, 2)  # bool вместо int (в Python bool наследуется от int, но для строгости считаем их разными)
    
    def test_incorrect_types_str(self):
        """Тест некорректных типов для str параметров"""
        
        @strict
        def process_string(text: str) -> str:
            return text.upper()
        
        with self.assertRaises(TypeError):
            process_string(123)  # int вместо str
        
        with self.assertRaises(TypeError):
            process_string(12.5)  # float вместо str
    
    def test_incorrect_types_float(self):
        """Тест некорректных типов для float параметров"""
        
        @strict
        def calculate(x: float, y: float) -> float:
            return x * y
        
        with self.assertRaises(TypeError):
            calculate(1, 2.5)  # int вместо float для первого аргумента
        
        with self.assertRaises(TypeError):
            calculate(2.5, "3")  # str вместо float для второго аргумента
    
    def test_incorrect_types_bool(self):
        """Тест некорректных типов для bool параметров"""
        
        @strict
        def logical_operation(flag: bool) -> bool:
            return not flag
        
        with self.assertRaises(TypeError):
            logical_operation(1)  # int вместо bool
        
        with self.assertRaises(TypeError):
            logical_operation("true")  # str вместо bool
    
    def test_mixed_types(self):
        """Тест функции со смешанными типами"""
        
        @strict
        def mixed_function(name: str, age: int, height: float, is_student: bool) -> str:
            return f"{name} is {age} years old, {height}m tall, student: {is_student}"
        
        # Корректный вызов
        result = mixed_function("Alice", 25, 1.65, True)
        expected = "Alice is 25 years old, 1.65m tall, student: True"
        self.assertEqual(result, expected)
        
        # Некорректные вызовы
        with self.assertRaises(TypeError):
            mixed_function(123, 25, 1.65, True)  # int вместо str
        
        with self.assertRaises(TypeError):
            mixed_function("Alice", 25.5, 1.65, True)  # float вместо int
        
        with self.assertRaises(TypeError):
            mixed_function("Alice", 25, "tall", True)  # str вместо float
        
        with self.assertRaises(TypeError):
            mixed_function("Alice", 25, 1.65, "yes")  # str вместо bool
    
    def test_keyword_arguments(self):
        """Тест именованных аргументов"""
        
        @strict
        def greet(name: str, age: int) -> str:
            return f"Hello {name}, you are {age}"
        
        # Корректные именованные аргументы
        self.assertEqual(greet(name="Bob", age=30), "Hello Bob, you are 30")
        self.assertEqual(greet(age=30, name="Bob"), "Hello Bob, you are 30")
        
        # Некорректные именованные аргументы
        with self.assertRaises(TypeError):
            greet(name=123, age=30)  # int вместо str
        
        with self.assertRaises(TypeError):
            greet(name="Bob", age="30")  # str вместо int
    
    def test_mixed_positional_and_keyword(self):
        """Тест смешанных позиционных и именованных аргументов"""
        
        @strict
        def calculate_grade(name: str, score: int, max_score: int) -> str:
            percentage = (score / max_score) * 100
            return f"{name}: {percentage:.1f}%"
        
        # Корректные вызовы
        self.assertEqual(calculate_grade("Alice", score=85, max_score=100), "Alice: 85.0%")
        self.assertEqual(calculate_grade("Bob", 90, max_score=100), "Bob: 90.0%")
        
        # Некорректные вызовы
        with self.assertRaises(TypeError):
            calculate_grade(123, score=85, max_score=100)  # int вместо str
        
        with self.assertRaises(TypeError):
            calculate_grade("Alice", score=85.5, max_score=100)  # float вместо int
    
    def test_no_annotations(self):
        """Тест функции без аннотаций типов"""
        
        @strict
        def no_types(a, b):
            return a + b
        
        # Должно работать без проверки типов
        self.assertEqual(no_types(1, 2), 3)
        self.assertEqual(no_types("hello", " world"), "hello world")
        self.assertEqual(no_types([1, 2], [3, 4]), [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main() 