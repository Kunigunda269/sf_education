import unittest
from solution import appearance


class TestAppearanceFunction(unittest.TestCase):
    
    def test_provided_test_cases(self):
        """Тест предоставленных тестовых случаев"""
        
        tests = [
            {'intervals': {'lesson': [1594663200, 1594666800],
                     'pupil': [1594663340, 1594663389, 1594663390, 1594663395, 1594663396, 1594666472],
                     'tutor': [1594663290, 1594663430, 1594663443, 1594666473]},
             'answer': 3117
            },
            {'intervals': {'lesson': [1594702800, 1594706400],
                     'pupil': [1594702789, 1594704500, 1594702807, 1594704542, 1594704512, 1594704513, 1594704564, 1594705150, 1594704581, 1594704582, 1594704734, 1594705009, 1594705095, 1594705096, 1594705106, 1594706480, 1594705158, 1594705773, 1594705849, 1594706480, 1594706500, 1594706875, 1594706502, 1594706503, 1594706524, 1594706524, 1594706579, 1594706641],
                     'tutor': [1594700035, 1594700364, 1594702749, 1594705148, 1594705149, 1594706463]},
            'answer': 3577
            },
            {'intervals': {'lesson': [1594692000, 1594695600],
                     'pupil': [1594692033, 1594696347],
                     'tutor': [1594692017, 1594692066, 1594692068, 1594696341]},
            'answer': 3565
            },
        ]
        
        for i, test in enumerate(tests):
            with self.subTest(test_case=i):
                result = appearance(test['intervals'])
                self.assertEqual(result, test['answer'])
    
    def test_no_overlap(self):
        """Тест случая, когда ученик и учитель не пересекаются"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1000, 1200],
            'tutor': [1300, 1500]
        }
        result = appearance(intervals)
        self.assertEqual(result, 0)
    
    def test_full_overlap(self):
        """Тест случая полного пересечения"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1000, 2000],
            'tutor': [1000, 2000]
        }
        result = appearance(intervals)
        self.assertEqual(result, 1000)
    
    def test_partial_overlap(self):
        """Тест частичного пересечения"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1000, 1500],
            'tutor': [1200, 1800]
        }
        result = appearance(intervals)
        self.assertEqual(result, 300)  # пересечение с 1200 по 1500
    
    def test_outside_lesson_time(self):
        """Тест случая, когда активность выходит за пределы урока"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [900, 2100],  # начинается до урока, заканчивается после
            'tutor': [950, 1500]   # начинается до урока
        }
        result = appearance(intervals)
        self.assertEqual(result, 500)  # пересечение с 1000 по 1500 (ограничено уроком)
    
    def test_multiple_intervals_pupil(self):
        """Тест с несколькими интервалами у ученика"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1000, 1200, 1300, 1500, 1600, 1800],
            'tutor': [1100, 1700]
        }
        result = appearance(intervals)
        # Пересечения: [1100, 1200] + [1300, 1500] + [1600, 1700] = 100 + 200 + 100 = 400
        self.assertEqual(result, 400)
    
    def test_multiple_intervals_tutor(self):
        """Тест с несколькими интервалами у учителя"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1100, 1700],
            'tutor': [1000, 1200, 1300, 1500, 1600, 1800]
        }
        result = appearance(intervals)
        # Пересечения: [1100, 1200] + [1300, 1500] + [1600, 1700] = 100 + 200 + 100 = 400
        self.assertEqual(result, 400)
    
    def test_multiple_intervals_both(self):
        """Тест с несколькими интервалами у обоих"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1000, 1300, 1500, 1800],
            'tutor': [1100, 1400, 1600, 1900]
        }
        result = appearance(intervals)
        # Пересечения: [1100, 1300] + [1600, 1800] = 200 + 200 = 400
        self.assertEqual(result, 400)
    
    def test_adjacent_intervals(self):
        """Тест соседних интервалов"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1000, 1200, 1200, 1400],  # соседние интервалы
            'tutor': [1100, 1300]
        }
        result = appearance(intervals)
        # Интервалы ученика объединяются в [1000, 1400]
        # Пересечение: [1100, 1300] = 200
        self.assertEqual(result, 200)
    
    def test_overlapping_intervals(self):
        """Тест пересекающихся интервалов"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1000, 1300, 1200, 1500],  # пересекающиеся интервалы
            'tutor': [1100, 1400]
        }
        result = appearance(intervals)
        # Интервалы ученика объединяются в [1000, 1500]
        # Пересечение: [1100, 1400] = 300
        self.assertEqual(result, 300)
    
    def test_empty_intervals(self):
        """Тест пустых интервалов"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [],
            'tutor': [1100, 1400]
        }
        result = appearance(intervals)
        self.assertEqual(result, 0)
        
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1100, 1400],
            'tutor': []
        }
        result = appearance(intervals)
        self.assertEqual(result, 0)
    
    def test_single_timestamp_intervals(self):
        """Тест с интервалами из одной временной метки (некорректные)"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1100],  # нет пары
            'tutor': [1200, 1400]
        }
        # Ожидаем ValueError из-за некорректных данных
        with self.assertRaises(ValueError):
            appearance(intervals)
    
    def test_zero_duration_intervals(self):
        """Тест интервалов нулевой длительности"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1200, 1200],  # нулевая длительность
            'tutor': [1200, 1400]
        }
        result = appearance(intervals)
        self.assertEqual(result, 0)
    
    def test_edge_case_lesson_boundaries(self):
        """Тест граничных случаев с временем урока"""
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [1000, 1000],  # в момент начала урока
            'tutor': [2000, 2000]   # в момент окончания урока
        }
        result = appearance(intervals)
        self.assertEqual(result, 0)
        
        intervals = {
            'lesson': [1000, 2000],
            'pupil': [999, 1001],   # захватывает начало урока
            'tutor': [1999, 2001]   # захватывает конец урока
        }
        result = appearance(intervals)
        self.assertEqual(result, 0)  # нет пересечения
    
    def test_complex_overlapping_scenario(self):
        """Тест сложного сценария с множественными пересечениями"""
        intervals = {
            'lesson': [0, 1000],
            'pupil': [100, 200, 150, 300, 400, 600, 550, 700],  # пересекающиеся интервалы
            'tutor': [50, 250, 450, 550, 650, 800]  # частично пересекаются
        }
        result = appearance(intervals)
        # Ученик: [100, 300] (объединенные), [400, 700] (объединенные)
        # Учитель: [50, 250], [450, 550], [650, 800]
        # Пересечения: [100, 250] + [450, 550] + [650, 700] = 150 + 100 + 50 = 300
        self.assertEqual(result, 300)


if __name__ == "__main__":
    unittest.main() 