import os
from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path, override=True)


APP_NAME: str = os.getenv("APP_NAME", "user-service")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./user_service.db")
