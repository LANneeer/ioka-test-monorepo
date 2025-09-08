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

    async def save(self, aggregate: Payment) -> Payment:
        now = datetime.now(timezone.utc)
        orm_obj: Optional[PaymentORM] = await self.session.get(PaymentORM, aggregate.id)
        if orm_obj is None:
            orm_obj = PaymentORM(
                id=aggregate.id,
                payer_id=aggregate.payer_id,
                payee_id=aggregate.payee_id,
                src_amount=aggregate.src_amount,
                src_currency=aggregate.src_currency,
                dst_amount=aggregate.dst_amount,
                dst_currency=aggregate.dst_currency,
                fx_rate=aggregate.fx_rate,
                fx_provider=aggregate.fx_provider,
                fx_at=aggregate.fx_at,
                description=aggregate.description,
                status=(aggregate.status.value if hasattr(aggregate.status, "value") else aggregate.status),
                is_reversal=aggregate.is_reversal,
                created_at=aggregate.created_at or now,
                updated_at=now,
            )
            self.session.add(orm_obj)
        else:
            orm_obj.payer_id = aggregate.payer_id
            orm_obj.payee_id = aggregate.payee_id
            orm_obj.src_amount = aggregate.src_amount
            orm_obj.src_currency = aggregate.src_currency
            orm_obj.dst_amount = aggregate.dst_amount
            orm_obj.dst_currency = aggregate.dst_currency
            orm_obj.fx_rate = aggregate.fx_rate
            orm_obj.fx_provider = aggregate.fx_provider
            orm_obj.fx_at = aggregate.fx_at
            orm_obj.description = aggregate.description
            orm_obj.status = (aggregate.status.value if hasattr(aggregate.status, "value") else aggregate.status)
            orm_obj.is_reversal = aggregate.is_reversal
            orm_obj.updated_at = now

        return self._to_domain(orm_obj)

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
