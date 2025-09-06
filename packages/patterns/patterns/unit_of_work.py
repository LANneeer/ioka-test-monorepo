from abc import ABC, abstractmethod
from contextlib import AbstractContextManager, AbstractAsyncContextManager
from typing import Generator, Iterable, Tuple

from .message import Event
from .repository import AbstractRepository
from .observability import ObservabilityHook, NoopHook


class AbstractUnitOfWork(AbstractContextManager["AbstractUnitOfWork"]):
    repositories: Tuple[AbstractRepository, ...] = ()

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args) -> None:
        self.rollback()

    def commit(self) -> None:
        self._commit()

    def rollback(self) -> None:
        self._rollback()

    @abstractmethod
    def _commit(self) -> None:
        raise NotImplementedError

    def _rollback(self) -> None:
        pass

    def collect_new_events(self) -> Generator[Event, None, None]:
        for repo in self.repositories:
            for agg in list(repo.seen):
                while agg.events:
                    yield agg.events.pop(0)


class AsyncAbstractUnitOfWork(AbstractAsyncContextManager["AsyncAbstractUnitOfWork"]):
    repositories: Tuple[AbstractRepository, ...] = ()

    def __init__(self) -> None:
        self._hook: ObservabilityHook = NoopHook()

    def set_observability_hook(self, hook: ObservabilityHook) -> None:
        self._hook = hook

    async def __aenter__(self) -> "AsyncAbstractUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        ...
    
    @abstractmethod
    async def _commit(self) -> None:
        ...

    @abstractmethod
    async def _rollback(self) -> None:
        ...

    async def commit(self) -> None:
        await self._commit()
        await self._hook.on_uow_commit()

    async def rollback(self) -> None:
        await self._rollback()
        await self._hook.on_uow_rollback()
    
    def collect_new_events(self) -> Generator[Event, None, None]:
        for repo in self.repositories:
            for agg in list(repo.seen):
                while agg.events:
                    yield agg.events.pop(0)

