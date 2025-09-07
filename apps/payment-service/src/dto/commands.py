from dataclasses import dataclass
from typing import Any
from patterns.message import Event, Command

from uuid import UUID


@dataclass(frozen=True, slots=True)
class PaymentCreated(Event):
    payment_id: UUID
    payer_id: UUID
    payee_id: UUID
    src_amount: str
    src_currency: str
    dst_amount: str
    dst_currency: str
    fx_rate: str
    fx_at: str


@dataclass(frozen=True, slots=True)
class PaymentStatusChanged(Event):
    payment_id: UUID
    old_status: str
    new_status: str


@dataclass(frozen=True, slots=True)
class PaymentRefunded(Event):
    payment_id: UUID
    original_payment_id: UUID


@dataclass(frozen=True, slots=True)
class CreatePayment(Command):
    payer_id: UUID
    payee_id: UUID
    src_amount: str
    src_currency: str
    dst_currency: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class MarkProcessing(Command):
    payment_id: UUID


@dataclass(frozen=True, slots=True)
class CompletePayment(Command):
    payment_id: UUID


@dataclass(frozen=True, slots=True)
class FailPayment(Command):
    payment_id: UUID


@dataclass(frozen=True, slots=True)
class RefundPayment(Command):
    payment_id: UUID
    original_payment_id: UUID
