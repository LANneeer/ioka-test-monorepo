from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from patterns.aggregator import AbstractAggregate

from src.dto.commands import (
    UserActivated,
    UserDeactivated,
    UserPasswordChanged,
    UserProfileUpdated,
    UserRegistered,
    UserRoleChanged,
)


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(AbstractAggregate):
    def __init__(
        self,
        *,
        user_id: UUID | None = None,
        email: str,
        username: str,
        password_hash: str,
        role: Role = Role.USER,
        locale: str = "en",
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__()
        now = datetime.now(timezone.utc)
        self._id: UUID = user_id or uuid4()
        self._email: str = email
        self._username: str = username
        self._password_hash: str = password_hash
        self._role: Role = role
        self._locale: str = locale
        self._is_active: bool = is_active
        self._created_at: datetime = created_at or now
        self._updated_at: datetime = updated_at or now


    @classmethod
    def create(
        cls,
        *,
        email: str,
        username: str,
        password_hash: str,
        role: Role = Role.USER,
        locale: str = "en",
    ):
        user = cls(
            email=email,
            username=username,
            password_hash=password_hash,
            role=role,
            locale=locale,
        )
        user._record_event(
            UserRegistered(
                user_id=user.id,
                email=user.email,
                username=user.username,
                role=user.role.value,
                locale=user.locale,
            )
        )
        return user

    @classmethod
    def restore(
        cls,
        *,
        user_id: UUID,
        email: str,
        username: str,
        password_hash: str,
        role: Role,
        locale: str,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
    ):
        return cls(
            user_id=user_id,
            email=email,
            username=username,
            password_hash=password_hash,
            role=role,
            locale=locale,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
        )

    @property
    def id(self) -> UUID: return self._id

    @property
    def email(self) -> str: return self._email

    @property
    def username(self) -> str: return self._username

    @property
    def role(self) -> Role: return self._role

    @property
    def locale(self) -> str: return self._locale

    @property
    def is_active(self) -> bool: return self._is_active

    @property
    def created_at(self) -> datetime: return self._created_at

    @property
    def updated_at(self) -> datetime: return self._updated_at

    def rename(self, new_username: str) -> None:
        if not new_username or len(new_username) < 3:
            raise ValueError("Username should be at least 3 characters")
        if new_username == self._username:
            return
        self._username = new_username
        self._touch()
        self._record_event(UserProfileUpdated(user_id=self.id, changes={"username": new_username}))

    def change_locale(self, new_locale: str) -> None:
        if not new_locale:
            raise ValueError("Locale should be non-empty")
        if new_locale == self._locale:
            return
        self._locale = new_locale
        self._touch()
        self._record_event(UserProfileUpdated(user_id=self.id, changes={"locale": new_locale}))

    def change_password_hash(self, new_password_hash: str) -> None:
        if not new_password_hash:
            raise ValueError("Password hash should be non-empty")
        self._password_hash = new_password_hash
        self._touch()
        self._record_event(UserPasswordChanged(user_id=self.id))

    def deactivate(self) -> None:
        if not self._is_active:
            return
        self._is_active = False
        self._touch()
        self._record_event(UserDeactivated(user_id=self.id))

    def activate(self) -> None:
        if self._is_active:
            return
        self._is_active = True
        self._touch()
        self._record_event(UserActivated(user_id=self.id))

    def promote_to_admin(self) -> None:
        if self._role == Role.ADMIN:
            return
        self._role = Role.ADMIN
        self._touch()
        self._record_event(UserRoleChanged(user_id=self.id, new_role=self._role.value))

    def _touch(self) -> None:
        self._updated_at = datetime.now(timezone.utc)
