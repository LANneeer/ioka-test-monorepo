from typing import Any, Protocol
from uuid import UUID

from patterns.unit_of_work import AbstractUnitOfWork
from src.domains.users.model import User, Role
from src.dto.commands import (
    ActivateUser,
    ChangeUserPassword,
    DeactivateUser,
    PromoteToAdmin,
    UpdateUserProfile,
    UserRegistered,
    UserProfileUpdated,
    UserPasswordChanged,
    UserActivated,
    UserDeactivated,
    UserRoleChanged,
    RegisterUser,
)


class Notifier(Protocol):
    def send(self, *, channel: str, message: str) -> None: ...


class Publisher(Protocol):
    def publish(self, topic: str, payload: dict[str, Any]) -> None: ...


def handle_register_user(cmd: RegisterUser, uow: AbstractUnitOfWork) -> UUID:
    if getattr(uow, "users").get_by_email(cmd.email):
        raise ValueError("Email already in use")
    if getattr(uow, "users").get_by_username(cmd.username):
        raise ValueError("Username already in use")

    user = User.create(
        email=cmd.email,
        username=cmd.username,
        password_hash=cmd.password_hash,
        role=Role.USER,
        locale=cmd.locale,
    )
    uow.users.add(user)
    uow.commit()
    return user.id


def handle_update_user_profile(cmd: UpdateUserProfile, uow: AbstractUnitOfWork) -> None:
    user = uow.users.get(cmd.user_id)
    if user is None:
        raise ValueError("User not found")

    if cmd.new_username:
        existing = uow.users.get_by_username(cmd.new_username)
        if existing and existing.id != user.id:
            raise ValueError("Username already in use")
        user.rename(cmd.new_username)

    if cmd.new_locale:
        user.change_locale(cmd.new_locale)

    uow.users.add(user)
    uow.commit()


def handle_change_user_password(cmd: ChangeUserPassword, uow: AbstractUnitOfWork) -> None:
    user = uow.users.get(cmd.user_id)
    if user is None:
        raise ValueError("User not found")

    user.change_password_hash(cmd.new_password_hash)
    uow.users.add(user)
    uow.commit()


def handle_activate_user(cmd: ActivateUser, uow: AbstractUnitOfWork) -> None:
    user = uow.users.get(cmd.user_id)
    if user is None:
        raise ValueError("User not found")

    user.activate()
    uow.users.add(user)
    uow.commit()


def handle_deactivate_user(cmd: DeactivateUser, uow: AbstractUnitOfWork) -> None:
    user = uow.users.get(cmd.user_id)
    if user is None:
        raise ValueError("User not found")

    user.deactivate()
    uow.users.add(user)
    uow.commit()


def handle_promote_to_admin(cmd: PromoteToAdmin, uow: AbstractUnitOfWork) -> None:
    user = uow.users.get(cmd.user_id)
    if user is None:
        raise ValueError("User not found")

    user.promote_to_admin()
    uow.users.add(user)
    uow.commit()


def on_user_registered(evt: UserRegistered, notifier: Notifier | None = None, publisher: Publisher | None = None) -> None:
    if notifier:
        notifier.send(channel="telegram", message=f"New user registered: {evt.username} ({evt.email})")
    if publisher:
        publisher.publish(topic="user.registered", payload={"user_id": str(evt.user_id), "email": evt.email})


def on_user_profile_updated(evt: UserProfileUpdated, publisher: Publisher | None = None) -> None:
    if publisher:
        publisher.publish(topic="user.profile_updated", payload={"user_id": str(evt.user_id), "changes": evt.changes})


def on_user_password_changed(evt: UserPasswordChanged, publisher: Publisher | None = None) -> None:
    if publisher:
        publisher.publish(topic="user.password_changed", payload={"user_id": str(evt.user_id)})


def on_user_activated(evt: UserActivated, publisher: Publisher | None = None) -> None:
    if publisher:
        publisher.publish(topic="user.activated", payload={"user_id": str(evt.user_id)})


def on_user_deactivated(evt: UserDeactivated, publisher: Publisher | None = None) -> None:
    if publisher:
        publisher.publish(topic="user.deactivated", payload={"user_id": str(evt.user_id)})


def on_user_role_changed(evt: UserRoleChanged, publisher: Publisher | None = None) -> None:
    if publisher:
        publisher.publish(topic="user.role_changed", payload={"user_id": str(evt.user_id), "role": evt.new_role})
