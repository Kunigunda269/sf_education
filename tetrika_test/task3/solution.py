def appearance(intervals):
    """
    Считает время когда ученик и учитель присутствовали одновременно на уроке.
    
    intervals - словарь с ключами:
    - lesson: [начало, конец] урока
    - pupil: [вход1, выход1, вход2, выход2, ...] ученика
    - tutor: [вход1, выход1, вход2, выход2, ...] учителя
    """
    
    # Получаем время урока
    lesson_start = intervals['lesson'][0]
    lesson_end = intervals['lesson'][1]
    
    # Получаем интервалы ученика
    pupil_times = intervals['pupil']
    pupil_intervals = []
    for i in range(0, len(pupil_times), 2):
        if i + 1 < len(pupil_times):
            start = pupil_times[i]
            end = pupil_times[i + 1]
            # Ограничиваем временем урока
            start = max(start, lesson_start)
            end = min(end, lesson_end)
            if start < end:
                pupil_intervals.append([start, end])
    
    # Получаем интервалы учителя
    tutor_times = intervals['tutor']
    tutor_intervals = []
    for i in range(0, len(tutor_times), 2):
        if i + 1 < len(tutor_times):
            start = tutor_times[i]
            end = tutor_times[i + 1]
            # Ограничиваем временем урока
            start = max(start, lesson_start)
            end = min(end, lesson_end)
            if start < end:
                tutor_intervals.append([start, end])
    
    # Объединяем пересекающиеся интервалы ученика
    pupil_merged = merge_intervals(pupil_intervals)
    
    # Объединяем пересекающиеся интервалы учителя  
    tutor_merged = merge_intervals(tutor_intervals)
    
    # Находим пересечения
    total_time = 0
    for pupil_interval in pupil_merged:
        for tutor_interval in tutor_merged:
            # Находим пересечение двух интервалов
            start = max(pupil_interval[0], tutor_interval[0])
            end = min(pupil_interval[1], tutor_interval[1])
            
            if start < end:
                total_time += end - start
    
    return total_time


def merge_intervals(intervals):
    """
    Объединяет пересекающиеся интервалы.
    """
    if not intervals:
        return []
    
    # Сортируем по началу интервала
    intervals.sort()
    
    merged = [intervals[0]]
    
    for current in intervals[1:]:
        last = merged[-1]
        
        # Если интервалы пересекаются или касаются
        if current[0] <= last[1]:
            # Объединяем
            merged[-1] = [last[0], max(last[1], current[1])]
        else:
            # Добавляем новый интервал
            merged.append(current)
    
    return merged


# Тесты из задания
tests = [
    {
        'intervals': {
            'lesson': [1594663200, 1594666800],
            'pupil': [1594663340, 1594663389, 1594663390, 1594663395, 1594663396, 1594666472],
            'tutor': [1594663290, 1594663430, 1594663443, 1594666473]
        },
        'answer': 3117
    },
    {
        'intervals': {
            'lesson': [1594702800, 1594706400],
            'pupil': [1594702789, 1594704500, 1594702807, 1594704542, 1594704512, 1594704513, 1594704564, 1594705150, 1594704581, 1594704582, 1594704734, 1594705009, 1594705095, 1594705096, 1594705106, 1594706480, 1594705158, 1594705773, 1594705849, 1594706480, 1594706500, 1594706875, 1594706502, 1594706503, 1594706524, 1594706524, 1594706579, 1594706641],
            'tutor': [1594700035, 1594700364, 1594702749, 1594705148, 1594705149, 1594706463]
        },
        'answer': 3577
    },
    {
        'intervals': {
            'lesson': [1594692000, 1594695600],
            'pupil': [1594692033, 1594696347],
            'tutor': [1594692017, 1594692066, 1594692068, 1594696341]
        },
        'answer': 3565
    }
]


if __name__ == '__main__':
    print("Тестирование функции appearance:")
    
    for i, test in enumerate(tests):
        result = appearance(test['intervals'])
        expected = test['answer']
        
        if result == expected:
            print(f"Тест {i + 1}: PASS - результат {result}")
        else:
            print(f"Тест {i + 1}: FAIL - ожидалось {expected}, получено {result}")
    
    print("Тестирование завершено!") 