from typing import Optional, Dict
from uuid import UUID

from patterns.repository import AbstractRepository
from src.domains.users.model import User


class InMemoryUserRepository(AbstractRepository[User]):
    def __init__(self) -> None:
        super().__init__()
        self._store: Dict[UUID, User] = {}

    def _add(self, aggregate: User) -> None:
        self._store[aggregate.id] = aggregate

    def _get(self, reference: UUID) -> Optional[User]:
        return self._store.get(reference)

    def get_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._store.values() if u.email == email), None)

    def get_by_username(self, username: str) -> Optional[User]:
        return next((u for u in self._store.values() if u.username == username), None)

    def list_users(self, skip: int = 0, limit: int = 50) -> list[User]:
        values = list(self._store.values())
        return values[skip : skip + limit]

    def remove(self, user_id: UUID) -> None:
        self._store.pop(user_id, None)
