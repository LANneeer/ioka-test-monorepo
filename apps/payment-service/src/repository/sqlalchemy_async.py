from typing import Optional, Sequence
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from patterns.repository import AbstractRepository
from src.infrastructure.payments.orm import PaymentORM, PaymentStatus
from src.domains.payments.model import Payment, Status
from datetime import datetime, timezone


class SqlAlchemyAsyncPaymentRepository(AbstractRepository[Payment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.session = session

    def _add(self, aggregate: Payment) -> None:
        self.session.add(self._to_orm(aggregate))

    def _get(self, reference: UUID) -> Optional[Payment]:
        raise NotImplementedError("Use async get_async")

    async def save(self, aggregate: Payment, *, commit: bool = False, refresh: bool = True) -> Payment:
        orm = self._to_orm(aggregate)
        self.session.add(orm)
        await self.session.flush()
        if commit:
            await self.session.commit()
        if refresh:
            await self.session.refresh(orm)
        return self._to_domain(orm)

    async def get_async(self, payment_id: UUID) -> Optional[Payment]:
        row = await self.session.get(PaymentORM, payment_id)
        return self._to_domain(row) if row else None

    async def list_payments(self, *, payer_id: UUID | None = None, payee_id: UUID | None = None, skip: int = 0, limit: int = 50) -> list[Payment]:
        q = select(PaymentORM).order_by(PaymentORM.created_at.desc())
        if payer_id: q = q.where(PaymentORM.payer_id == payer_id)
        if payee_id: q = q.where(PaymentORM.payee_id == payee_id)
        res = await self.session.execute(q.offset(skip).limit(limit))
        rows: Sequence[PaymentORM] = res.scalars().all()
        return [self._to_domain(r) for r in rows]

    async def remove(self, payment_id: UUID) -> None:
        await self.session.execute(delete(PaymentORM).where(PaymentORM.id == payment_id))

    @staticmethod
    def _to_domain(row: PaymentORM) -> Payment:
        return Payment.restore(
            payment_id=row.id,
            payer_id=row.payer_id,
            payee_id=row.payee_id,
            src_amount=Decimal(str(row.src_amount)),
            src_currency=row.src_currency,
            dst_amount=Decimal(str(row.dst_amount)),
            dst_currency=row.dst_currency,
            fx_rate=Decimal(str(row.fx_rate)),
            fx_provider=row.fx_provider,
            fx_at=row.fx_at,
            description=row.description,
            status=Status(row.status.value if hasattr(row.status, "value") else row.status),
            is_reversal=row.is_reversal,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_orm(agg: Payment) -> PaymentORM:
        return PaymentORM(
            id=agg.id,
            payer_id=agg.payer_id,
            payee_id=agg.payee_id,
            src_amount=agg.src_amount,
            src_currency=agg.src_currency,
            dst_amount=agg.dst_amount,
            dst_currency=agg.dst_currency,
            fx_rate=agg.fx_rate,
            fx_provider=agg.fx_provider,
            fx_at=agg.fx_at,
            description=agg.description,
            status=PaymentStatus(agg.status.value),
            is_reversal=agg.is_reversal,
            created_at=agg.created_at,
            updated_at=agg.updated_at,
        )
