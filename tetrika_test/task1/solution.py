import functools


def strict(func):
    """
    Декоратор для проверки типов аргументов функции.
    Проверяет, что переданные аргументы соответствуют аннотациям типов.
    """
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Получаем аннотации типов
        annotations = func.__annotations__
        
        # Если нет аннотаций, просто вызываем функцию
        if not annotations:
            return func(*args, **kwargs)
        
        # Получаем имена параметров функции
        import inspect
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        
        # Проверяем позиционные аргументы
        for i, arg_value in enumerate(args):
            if i < len(param_names):
                param_name = param_names[i]
                if param_name in annotations:
                    expected_type = annotations[param_name]
                    actual_type = type(arg_value)
                    
                    if actual_type != expected_type:
                        raise TypeError(
                            f"Argument '{param_name}' must be {expected_type.__name__}, "
                            f"got {actual_type.__name__}"
                        )
        
        # Проверяем именованные аргументы
        for param_name, arg_value in kwargs.items():
            if param_name in annotations:
                expected_type = annotations[param_name]
                actual_type = type(arg_value)
                
                if actual_type != expected_type:
                    raise TypeError(
                        f"Argument '{param_name}' must be {expected_type.__name__}, "
                        f"got {actual_type.__name__}"
                    )
        
        return func(*args, **kwargs)
    
    return wrapper


@strict
def sum_two(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    # Тестируем корректный вызов
    print(sum_two(1, 2))  # Должно работать
    
    # Тестируем некорректные вызовы
    try:
        sum_two(1, 2.4)  # float вместо int
    except TypeError as e:
        print(f"Ошибка: {e}")
    
    try:
        sum_two("1", 2)  # str вместо int
    except TypeError as e:
        print(f"Ошибка: {e}")
    
    try:
        sum_two(True, 2)  # bool вместо int
    except TypeError as e:
        print(f"Ошибка: {e}") 