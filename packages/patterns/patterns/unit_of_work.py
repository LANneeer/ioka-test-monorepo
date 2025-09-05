from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Generator, Iterable, Tuple

from .message import Event
from .repository import AbstractRepository


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
