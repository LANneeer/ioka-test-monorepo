from typing import Any, Protocol
from uuid import UUID
from patterns.unit_of_work import AsyncAbstractUnitOfWork
from src.domains.users.model import User, Role, UserRegistered, UserProfileUpdated, UserPasswordChanged, UserActivated, UserDeactivated, UserRoleChanged
from src.dto.commands import RegisterUser, UpdateUserProfile, ChangeUserPassword, ActivateUser, DeactivateUser, PromoteToAdmin
from src.domains.common.exceptions import DuplicateEmail, DuplicateUsername, NotFound, Conflict

class Notifier(Protocol):
    async def send(self, *, channel: str, message: str) -> None: ...

class Publisher(Protocol):
    async def publish(self, topic: str, payload: dict[str, Any]) -> None: ...

async def handle_register_user(cmd: RegisterUser, uow: AsyncAbstractUnitOfWork) -> UUID:
    if await uow.users.get_by_email(cmd.email):
        raise DuplicateEmail("Email already in use")
    if await uow.users.get_by_username(cmd.username):
        raise DuplicateUsername("Username already in use")

    user = User.create(email=cmd.email, username=cmd.username, password_hash=cmd.password_hash, role=Role.USER, locale=cmd.locale)
    uow.users.add(user)
    await uow.commit()
    return user.id

async def handle_update_user_profile(cmd: UpdateUserProfile, uow: AsyncAbstractUnitOfWork) -> None:
    user = await uow.users.get_async(cmd.user_id)
    if not user:
        raise NotFound("User not found")
    if cmd.new_username:
        existing = await uow.users.get_by_username(cmd.new_username)
        if existing and existing.id != user.id:
            raise Conflict("Username already in use")
        user.rename(cmd.new_username)
    if cmd.new_locale:
        user.change_locale(cmd.new_locale)
    await uow.users.save(user)
    await uow.commit()

async def handle_change_user_password(cmd: ChangeUserPassword, uow: AsyncAbstractUnitOfWork) -> None:
    user = await uow.users.get_async(cmd.user_id)
    if not user:
        raise NotFound("User not found")
    user.change_password_hash(cmd.new_password_hash)
    await uow.users.save(user)
    await uow.commit()

async def handle_activate_user(cmd: ActivateUser, uow: AsyncAbstractUnitOfWork) -> None:
    user = await uow.users.get_async(cmd.user_id)
    if not user:
        raise NotFound("User not found")
    user.activate()
    await uow.users.save(user)
    await uow.commit()

async def handle_deactivate_user(cmd: DeactivateUser, uow: AsyncAbstractUnitOfWork) -> None:
    user = await uow.users.get_async(cmd.user_id)
    if not user:
        raise NotFound("User not found")
    user.deactivate()
    await uow.users.save(user)
    await uow.commit()

async def handle_promote_to_admin(cmd: PromoteToAdmin, uow: AsyncAbstractUnitOfWork) -> None:
    user = await uow.users.get_async(cmd.user_id)
    if not user:
        raise NotFound("User not found")
    user.promote_to_admin()
    await uow.users.save(user)
    await uow.commit()

async def on_user_registered(evt: UserRegistered, notifier: Notifier | None = None, publisher: Publisher | None = None) -> None:
    if notifier:
        await notifier.send(channel="telegram", message=f"New user registered: {evt.username} ({evt.email})")
    if publisher:
        await publisher.publish(topic="user.registered", payload={"user_id": str(evt.user_id), "email": evt.email})
