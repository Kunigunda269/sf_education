# API-сервис бронирования столиков в ресторане

REST API для бронирования столиков в ресторане. Сервис позволяет создавать, просматривать и удалять брони, а также управлять столиками и временными слотами.

## Функциональность

### Столики
- Создание столиков с указанием количества мест и расположения
- Просмотр списка всех столиков
- Удаление столиков

### Бронирования
- Создание бронирований с проверкой доступности столика
- Просмотр списка всех бронирований
- Удаление бронирований

### Валидация
- Проверка конфликтов бронирований
- Валидация входных данных
- Обработка ошибок

## Технический стек

- FastAPI - основной фреймворк
- SQLAlchemy - ORM для работы с базой данных
- PostgreSQL - база данных
- Alembic - миграции базы данных
- Docker - контейнеризация
- Pytest - тестирование

## Установка и запуск

1. Клонировать репозиторий:
```bash
git clone <repository-url>
cd test_stoliki
```

2. Запустить сервисы через Docker Compose:
```bash
docker-compose up -d
```

3. Выполнить миграции:
```bash
docker-compose exec api alembic upgrade head
```

4. API будет доступно по адресу: http://localhost:8000
5. Документация API доступна по адресу: http://localhost:8000/docs

## API Endpoints

### Столики
- `GET /tables/` - получить список всех столиков
- `POST /tables/` - создать новый столик
- `DELETE /tables/{id}` - удалить столик

### Бронирования
- `GET /reservations/` - получить список всех бронирований
- `POST /reservations/` - создать новое бронирование
- `DELETE /reservations/{id}` - удалить бронирование

## Тестирование

Для запуска тестов выполните:
```bash
docker-compose exec api pytest
```

## Структура проекта

```
test_stoliki/
├── app/
│   ├── models/
│   │   └── models.py
│   ├── schemas/
│   │   └── schemas.py
│   ├── services/
│   │   ├── table_service.py
│   │   └── reservation_service.py
│   ├── routers/
│   │   ├── table_router.py
│   │   └── reservation_router.py
│   ├── database.py
│   └── main.py
├── migrations/
│   ├── versions/
│   │   └── initial_migration.py
│   ├── env.py
│   └── script.py.mako
├── tests/
│   ├── test_services.py
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── README.md
``` 