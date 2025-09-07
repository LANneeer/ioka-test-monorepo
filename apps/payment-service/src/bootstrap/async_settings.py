from typing import Mapping, Sequence, Type
from patterns.message import Command, Event
from patterns.message_bus import AsyncMessageBus
from patterns.unit_of_work import AsyncAbstractUnitOfWork
from patterns.observability import ObservabilityHook

from src.dto.commands import (
    CreatePayment, MarkProcessing, CompletePayment, FailPayment, RefundPayment, 
        PaymentCreated, PaymentStatusChanged, PaymentRefunded
)
from src.gateway.handlers.async_payment import (
    handle_create_payment, handle_mark_processing, handle_complete, handle_fail, handle_refund,
    on_payment_created, on_payment_status_changed, on_payment_refunded
)

def bootstrap_async(
    uow: AsyncAbstractUnitOfWork,
    hook: ObservabilityHook | None = None,
    **deps,
) -> AsyncMessageBus:
    if hook is not None:
        uow.set_observability_hook(hook)
    event_handlers: Mapping[Type[Event], Sequence] = {
        PaymentCreated: [on_payment_created],
        PaymentStatusChanged: [on_payment_status_changed],
        PaymentRefunded: [on_payment_refunded],
    }
    command_handlers: Mapping[Type[Command], callable] = {
        CreatePayment: handle_create_payment,
        MarkProcessing: handle_mark_processing,
        CompletePayment: handle_complete,
        FailPayment: handle_fail,
        RefundPayment: handle_refund,
    }
    return AsyncMessageBus(
        uow=uow,
        event_handlers=event_handlers,
        command_handlers=command_handlers,
        dependencies=deps,
        raise_on_error=True,
        hook=hook,
    )
