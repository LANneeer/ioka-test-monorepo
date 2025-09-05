from dataclasses import dataclass
from typing import Any
from patterns.message import Event, Command

from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserRegistered(Event):
    user_id: UUID
    email: str
    username: str
    role: str
    locale: str


@dataclass(frozen=True, slots=True)
class UserProfileUpdated(Event):
    user_id: UUID
    changes: dict[str, Any]


@dataclass(frozen=True, slots=True)
class UserPasswordChanged(Event):
    user_id: UUID


@dataclass(frozen=True, slots=True)
class UserActivated(Event):
    user_id: UUID


@dataclass(frozen=True, slots=True)
class UserDeactivated(Event):
    user_id: UUID


@dataclass(frozen=True, slots=True)
class UserRoleChanged(Event):
    user_id: UUID
    new_role: str


@dataclass(frozen=True, slots=True)
class RegisterUser(Command):
    email: str
    username: str
    password_hash: str
    locale: str = "en"


@dataclass(frozen=True, slots=True)
class UpdateUserProfile(Command):
    user_id: UUID
    new_username: str | None = None
    new_locale: str | None = None


@dataclass(frozen=True, slots=True)
class ChangeUserPassword(Command):
    user_id: UUID
    new_password_hash: str


@dataclass(frozen=True, slots=True)
class ActivateUser(Command):
    user_id: UUID


@dataclass(frozen=True, slots=True)
class DeactivateUser(Command):
    user_id: UUID


@dataclass(frozen=True, slots=True)
class PromoteToAdmin(Command):
    user_id: UUID
