import os
from pathlib import Path

from pydantic import BaseModel
from dotenv import load_dotenv

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path, override=True)

class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "users-service")
    ENV: str = os.getenv("ENV", "local")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./payment_service.db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOGSTASH_HOST: str | None = os.getenv("LOGSTASH_HOST")
    LOGSTASH_PORT: int = int(os.getenv("LOGSTASH_PORT", "5044"))
    REQUEST_ID_HEADER: str = os.getenv("REQUEST_ID_HEADER", "X-Request-ID")

    PROM_ENABLED: bool = os.getenv("PROM_ENABLED", "1") == "1"

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    IDEMPOTENCY_TTL_SEC: int = int(os.getenv("IDEMPOTENCY_TTL_SEC", "600"))

    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")
    EMAIL_SMTP_HOST: str | None = os.getenv("EMAIL_SMTP_HOST")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_USER: str | None = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD: str | None = os.getenv("EMAIL_PASSWORD")

    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "payment-service")
    TRACING_ENABLED: bool = os.getenv("TRACING_ENABLED", "0") == "1"
    TRACING_ENDPOINT: str | None = os.getenv("TRACING_ENDPOINT")

settings = Settings()
