# payment-service

Сервис платежей: переводы, мультивалютность, комиссии, refund.

## Запуск
```bash
poetry install
poetry run uvicorn src.cli.fastapi_app:app --reload --port 8002
```
API доступен по адресу: http://localhost:8002

## Структура
payment-service
├── src/
│   ├── domains/ # модель Payment, интерфейсы, сервис
│   ├── dto/ # команды и события (PaymentCreated, etc.)
│   ├── gateway/ # схемы для FastAPI
│   ├── infrastructure/ # ORM, UoW, интеграции с FX API
│   └── cli/ # fastapi_app
└── README.md

## Возможности
Создание платежа с автоматической конвертацией валют
Поддержка комиссий (фиксированные и процентные)
Изменение статуса (processing, completed, failed, refunded)
Refund = обратная операция (реверс транзакции)
Хранение истории статусов

## Observability
Логи → Logstash
Метрики → Prometheus /metrics
Аудит транзакций

---
