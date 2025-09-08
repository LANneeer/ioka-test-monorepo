# user-service

Сервис пользователей: регистрация, авторизация, профили.

## Запуск
```bash
poetry install
poetry run uvicorn src.cli.fastapi_app:app --reload --port 8001
```
API доступен по адресу: http://localhost:8001

## Структура
user-service
├── src/
│   ├── domains/ # модель User, интерфейсы, сервис
│   ├── dto/ # команды и события
│   ├── gateway/ # схемы для FastAPI
│   ├── infrastructure/ # ORM, UoW, middleware
│   └── cli/ # fastapi_app и demo_app
└── README.md

## Возможности
Регистрация нового пользователя
Получение списка и профиля
Активация/деактивация
Смена пароля
Повышение до администратора

## Observability
Логи → Logstash
Метрики → Prometheus /metrics
Аудит операций

---
