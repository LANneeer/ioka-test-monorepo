from typing import Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from patterns.repository import AbstractRepository
from patterns.unit_of_work import AsyncAbstractUnitOfWork
from patterns.observability import ObservabilityHook, NoopHook
from src.infrastructure.db_async import AsyncSessionLocal
from src.repository.sqlalchemy_async import SqlAlchemyAsyncPaymentRepository
from src.domains.common.exceptions import  DatabaseConflict


class AsyncUnitOfWork(AsyncAbstractUnitOfWork):
    def __init__(self, session_factory=AsyncSessionLocal) -> None:
        super().__init__()
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "AsyncUnitOfWork":
        self.session = self._session_factory()
        self.payments = SqlAlchemyAsyncPaymentRepository(self.session)
        self.repositories: Tuple[AbstractRepository, ...] = (self.payments,)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc:
                await self.rollback()
            else:
                await self.commit()
        finally:
            if self.session:
                await self.session.close()

    async def _commit(self) -> None:
        try:
            if self.session:
                await self.session.commit()
        except IntegrityError as e:
            raise DatabaseConflict("Database conflict")

    async def _rollback(self) -> None:
        if self.session:
            await self.session.rollback()
