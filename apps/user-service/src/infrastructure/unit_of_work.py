from typing import Tuple

from patterns.unit_of_work import AbstractUnitOfWork
from patterns.repository import AbstractRepository
from src.repository.user_in_memory import InMemoryUserRepository


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        super().__init__()
        self.users = InMemoryUserRepository()
        self.repositories: Tuple[AbstractRepository, ...] = (self.users,)

    def __enter__(self) -> "InMemoryUnitOfWork":
        return super().__enter__()

    def _commit(self) -> None:
        pass

    def _rollback(self) -> None:
        self.users.seen.clear()
