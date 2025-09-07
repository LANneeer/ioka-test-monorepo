from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from patterns.aggregator import AbstractAggregate
from patterns.message import Event

from src.dto.commands import (
    PaymentCreated,
    PaymentRefunded,
    PaymentStatusChanged
)

class Status(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(AbstractAggregate):
    def __init__(
        self,
        *,
        payment_id: UUID | None = None,
        payer_id: UUID,
        payee_id: UUID,
        src_amount: Decimal,
        src_currency: str,
        dst_amount: Decimal,
        dst_currency: str,
        fx_rate: Decimal,
        fx_provider: str,
        fx_at: datetime,
        description: str | None = None,
        status: Status = Status.CREATED,
        is_reversal: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__()
        now = datetime.now(timezone.utc)
        self._id: UUID = payment_id or uuid4()

        self._payer_id = payer_id
        self._payee_id = payee_id

        self._src_amount = src_amount
        self._src_currency = src_currency.upper()
        self._dst_amount = dst_amount
        self._dst_currency = dst_currency.upper()

        self._fx_rate = fx_rate
        self._fx_provider = fx_provider
        self._fx_at = fx_at

        self._description = description
        self._status = status
        self._is_reversal = is_reversal
        self._created_at = created_at or now
        self._updated_at = updated_at or now


    @classmethod
    def create_with_quote(
        cls,
        *,
        payer_id: UUID,
        payee_id: UUID,
        src_amount: Decimal,
        src_currency: str,
        dst_amount: Decimal,
        dst_currency: str,
        fx_rate: Decimal,
        fx_provider: str,
        fx_at: datetime,
        description: str | None = None,
    ) -> "Payment":
        if src_amount <= 0:
            raise ValueError("Amount must be positive")

        obj = cls(
            payer_id=payer_id,
            payee_id=payee_id,
            src_amount=src_amount,
            src_currency=src_currency,
            dst_amount=dst_amount,
            dst_currency=dst_currency,
            fx_rate=fx_rate,
            fx_provider=fx_provider,
            fx_at=fx_at,
            description=description,
        )
        obj._record_event(
            PaymentCreated(
                payment_id=obj.id,
                payer_id=payer_id,
                payee_id=payee_id,
                src_amount=str(src_amount),
                src_currency=obj._src_currency,
                dst_amount=str(dst_amount),
                dst_currency=obj._dst_currency,
                fx_rate=str(fx_rate),
                fx_at=fx_at.isoformat(),
            )
        )
        return obj

    @property
    def id(self) -> UUID: return self._id
    @property
    def payer_id(self) -> UUID: return self._payer_id
    @property
    def payee_id(self) -> UUID: return self._payee_id
    @property
    def src_amount(self) -> Decimal: return self._src_amount
    @property
    def src_currency(self) -> str: return self._src_currency
    @property
    def dst_amount(self) -> Decimal: return self._dst_amount
    @property
    def dst_currency(self) -> str: return self._dst_currency
    @property
    def fx_rate(self) -> Decimal: return self._fx_rate
    @property
    def fx_provider(self) -> str: return self._fx_provider
    @property
    def fx_at(self) -> datetime: return self._fx_at
    @property
    def description(self) -> str | None: return self._description
    @property
    def status(self) -> Status: return self._status
    @property
    def is_reversal(self) -> bool: return self._is_reversal
    @property
    def created_at(self) -> datetime: return self._created_at
    @property
    def updated_at(self) -> datetime: return self._updated_at
    @classmethod
    def restore(cls, **state: Any) -> "Payment":
        return cls(**state)

    def mark_processing(self) -> None:
        self._transition(Status.PROCESSING)

    def complete(self) -> None:
        self._transition(Status.COMPLETED)

    def fail(self) -> None:
        self._transition(Status.FAILED)

    def refund(self, *, original_payment_id: UUID) -> None:
        if self._status != Status.COMPLETED:
            raise ValueError("Only completed payments can be refunded")
        self._is_reversal = True
        self._transition(Status.REFUNDED)
        self._record_event(PaymentRefunded(payment_id=self.id, original_payment_id=original_payment_id))

    def _transition(self, new_status: Status) -> None:
        if self._status == new_status:
            return
        old = self._status
        self._status = new_status
        self._updated_at = datetime.now(timezone.utc)
        self._record_event(PaymentStatusChanged(payment_id=self.id, old_status=old.value, new_status=new_status.value))

