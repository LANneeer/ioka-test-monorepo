from typing import Sequence, Mapping, Type

from patterns.message_bus import MessageBus
from patterns.message import Command, Event
from patterns.unit_of_work import AbstractUnitOfWork

from src.dto.commands import (
    RegisterUser,
    UpdateUserProfile,
    ChangeUserPassword,
    ActivateUser,
    DeactivateUser,
    PromoteToAdmin,
)
from src.gateway.handlers.user import (
    handle_register_user,
    handle_update_user_profile,
    handle_change_user_password,
    handle_activate_user,
    handle_deactivate_user,
    handle_promote_to_admin,
    on_user_registered,
    on_user_profile_updated,
    on_user_password_changed,
    on_user_activated,
    on_user_deactivated,
    on_user_role_changed,
)
from src.dto.commands import (
    UserRegistered,
    UserProfileUpdated,
    UserPasswordChanged,
    UserActivated,
    UserDeactivated,
    UserRoleChanged,
)


def bootstrap(uow: AbstractUnitOfWork, **deps) -> MessageBus:
    event_handlers: Mapping[Type[Event], Sequence] = {
        UserRegistered: [on_user_registered],
        UserProfileUpdated: [on_user_profile_updated],
        UserPasswordChanged: [on_user_password_changed],
        UserActivated: [on_user_activated],
        UserDeactivated: [on_user_deactivated],
        UserRoleChanged: [on_user_role_changed],
    }

    command_handlers: Mapping[Type[Command], callable] = {
        RegisterUser: handle_register_user,
        UpdateUserProfile: handle_update_user_profile,
        ChangeUserPassword: handle_change_user_password,
        ActivateUser: handle_activate_user,
        DeactivateUser: handle_deactivate_user,
        PromoteToAdmin: handle_promote_to_admin,
    }

    bus = MessageBus(
        uow=uow,
        event_handlers=event_handlers,
        command_handlers=command_handlers,
        dependencies=deps,
        raise_on_error=True,
    )
    return bus
