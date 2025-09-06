from typing import Mapping, Sequence, Type
from patterns.message import Command, Event
from patterns.message_bus import AsyncMessageBus
from patterns.unit_of_work import AsyncAbstractUnitOfWork
from patterns.observability import ObservabilityHook
from src.dto.commands import RegisterUser, UpdateUserProfile, ChangeUserPassword, ActivateUser, DeactivateUser, PromoteToAdmin
from src.gateway.handlers.async_user import (
    handle_register_user, handle_update_user_profile, handle_change_user_password,
    handle_activate_user, handle_deactivate_user, handle_promote_to_admin,
    on_user_registered,
)
from src.dto.commands import UserRegistered

def bootstrap_async(uow: AsyncAbstractUnitOfWork, hook: ObservabilityHook | None = None, **deps) -> AsyncMessageBus:
    event_handlers: Mapping[Type[Event], Sequence] = {
        UserRegistered: [on_user_registered],
    }
    command_handlers: Mapping[Type[Command], callable] = {
        RegisterUser: handle_register_user,
        UpdateUserProfile: handle_update_user_profile,
        ChangeUserPassword: handle_change_user_password,
        ActivateUser: handle_activate_user,
        DeactivateUser: handle_deactivate_user,
        PromoteToAdmin: handle_promote_to_admin,
    }
    return AsyncMessageBus(
        uow=uow,
        event_handlers=event_handlers,
        command_handlers=command_handlers,
        dependencies=deps,
        raise_on_error=True,
        hook=hook
    )
