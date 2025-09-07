from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol, Optional
from uuid import UUID

from src.domains.payments.model import Payment


class IPaymentRepository(Protocol):
    def add(self, aggregate: Payment) -> None: ...
    async def get_async(self, payment_id: UUID) -> Optional[Payment]: ...
    async def list_payments(
        self,
        *,
        payer_id: UUID | None = None,
        payee_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Payment]: ...
    async def remove(self, payment_id: UUID) -> None: ...


class IUsersClient(Protocol):
    async def user_exists(self, user_id: UUID) -> bool: ...

@dataclass(frozen=True, slots=True)
class FxQuote:
    base: str
    quote: str
    rate: Decimal
    amount_in: Decimal
    amount_out: Decimal
    provider: str
    as_of: datetime

class IFxClient(Protocol):
    async def convert(self, *, base: str, quote: str, amount: Decimal) -> FxQuote: ...

class INotifier(Protocol):
    async def transaction_status(self, *, tx_id: str, status: str, amount: str, from_acc: str, to_acc: str) -> None: ...
