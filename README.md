# ioka-two

Моно-репозиторий микросервисов для платформы валютных переводов и управления пользователями.

## Структура репозитория
ioka-two
├── apps/ # все сервисы
│ ├── user-service # сервис пользователей и аутентификации
│ ├── payment-service # сервис платежей и конвертации валют
│ └── alert-service # (план) уведомления через Telegram и др.
├── packages/ # переиспользуемые библиотеки и паттерны
│ ├── patterns # core: aggregate, uow, repository, message bus, observability
│ └── utils # утилиты (api-интеграции)
├── observability/ # конфигурации для мониторинга и сбора метрик
├── docker-compose.yaml # локальная разработка
└── README.md # описание проекта

## Запуск локально
```bash
docker compose up --build
```

## Сервисы:
user-service: http://localhost:8001
payment-service: http://localhost:8002
Postgres: localhost:5432
Redis: localhost:6379
Kibana: http://localhost:5601
Grafana: http://localhost:3000
Prometheus: http://localhost:9090

## Observability
Логи → Logstash → Elasticsearch → Kibana
Метрики → Prometheus → Grafana

## Основные фичи
Users: регистрация, активация, авторизация
Payments: переводы, конвертация валют, live-курс валют, refund
Observability: аудит, метрики, логи, кэширование

---

