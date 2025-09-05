from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base
from src.config import DATABASE_URL

Base = declarative_base()

def _get_url() -> str:
    return DATABASE_URL

ASYNC_ENGINE: AsyncEngine = create_async_engine(
    _get_url(),
    future=True,
)
AsyncSessionLocal = async_sessionmaker(bind=ASYNC_ENGINE, expire_on_commit=False, autoflush=False, class_=AsyncSession)
