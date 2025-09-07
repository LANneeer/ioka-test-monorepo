from enum import Enum
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Enum as SAEnum, Index, String, text, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from src.infrastructure.db_async import Base

class PaymentStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentORM(Base):
    __tablename__ = "payments"
    id = Column(PG_UUID, primary_key=True)
    src_amount = Column(Numeric(18, 2), nullable=False)
    src_currency = Column(String(3), nullable=False)
    dst_amount = Column(Numeric(18, 2), nullable=False)
    dst_currency = Column(String(3), nullable=False)

    payer_id = Column(PG_UUID, nullable=True)
    payee_id = Column(PG_UUID, nullable=True)

    fx_rate = Column(Numeric(18, 8), nullable=False)
    fx_provider = Column(String(64), nullable=False)
    fx_at = Column(DateTime(timezone=True), nullable=False)

    description = Column(String(255), nullable=True)
    status = Column(SAEnum(PaymentStatus, name="payment_status"), nullable=False, server_default="CREATED")
    is_reversal = Column(Boolean, nullable=False, server_default=text("false"))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index("ix_payments_payer", "payer_id"),
        Index("ix_payments_payee", "payee_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_dst_ccy", "dst_currency"),
    )
