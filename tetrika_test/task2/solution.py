import requests
import csv
import time


def get_animals_from_wikipedia():
    """
    Получает список животных с Википедии и считает их по буквам.
    """
    
    # Настройки
    api_url = "https://ru.wikipedia.org/w/api.php"
    russian_letters = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ"
    
    # Счетчики для каждой буквы
    animal_count = {}
    for letter in russian_letters:
        animal_count[letter] = 0
    
    # Параметры запроса
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'categorymembers',
        'cmtitle': 'Категория:Животные по алфавиту',
        'cmlimit': 500
    }
    
    page_number = 0
    continue_token = None
    
    print("Начинаем получение данных...")
    
    # Основной цикл
    while page_number < 100:  # Ограничиваем количество страниц
        page_number += 1
        print(f"Обрабатываем страницу {page_number}...")
        
        # Добавляем токен продолжения если есть
        if continue_token:
            params['cmcontinue'] = continue_token
        
        try:
            # Делаем запрос
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Проверяем что получили данные
            if 'query' not in data or 'categorymembers' not in data['query']:
                print("Нет данных в ответе")
                break
                
            members = data['query']['categorymembers']
            print(f"Получено {len(members)} записей")
            
            # Обрабатываем каждое животное
            for member in members:
                title = member.get('title', '')
                if title:
                    first_letter = title[0].upper()
                    if first_letter in russian_letters:
                        animal_count[first_letter] += 1
            
            # Проверяем есть ли еще страницы
            if 'continue' in data and 'cmcontinue' in data['continue']:
                continue_token = data['continue']['cmcontinue']
                time.sleep(0.5)  # Небольшая пауза
            else:
                print("Достигнут конец списка")
                break
                
        except Exception as e:
            print(f"Ошибка: {e}")
            break
    
    return animal_count


def save_to_csv(animal_count):
    """
    Сохраняет результаты в CSV файл.
    """
    filename = "beasts.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Записываем только буквы с животными
            for letter in sorted(animal_count.keys()):
                count = animal_count[letter]
                if count > 0:
                    writer.writerow([letter, count])
        
        print(f"Результаты сохранены в {filename}")
        
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")


def main():
    """
    Главная функция.
    """
    print("=== Парсер животных с Википедии ===")
    
    # Получаем данные
    animal_count = get_animals_from_wikipedia()
    
    # Показываем результаты
    print("\nРезультаты:")
    total = 0
    for letter in sorted(animal_count.keys()):
        count = animal_count[letter]
        if count > 0:
            print(f"{letter}: {count}")
            total += count
    
    print(f"\nВсего животных: {total}")
    
    # Сохраняем в файл
    save_to_csv(animal_count)


if __name__ == "__main__":
    main() 