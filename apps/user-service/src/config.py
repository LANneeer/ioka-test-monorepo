import os
from pathlib import Path

from pydantic import BaseModel
from dotenv import load_dotenv

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path, override=True)

class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "user-service")
    ENV: str = os.getenv("ENV", "local")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./user_service.db")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOGSTASH_HOST: str | None = os.getenv("LOGSTASH_HOST")
    LOGSTASH_PORT: int = int(os.getenv("LOGSTASH_PORT", "5044"))
    REQUEST_ID_HEADER: str = os.getenv("REQUEST_ID_HEADER", "X-Request-ID")

    PROM_ENABLED: bool = os.getenv("PROM_ENABLED", "1") == "1"

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

settings = Settings()
