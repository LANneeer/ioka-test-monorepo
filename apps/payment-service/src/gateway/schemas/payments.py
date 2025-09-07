from pydantic import BaseModel, Field
from uuid import UUID

class PaymentCreateDTO(BaseModel):
    payer_id: UUID
    payee_id: UUID
    src_amount: str = Field(min_length=3, max_length=3)
    src_currency: str = Field(min_length=3, max_length=3)
    dst_currency: str = Field(min_length=3, max_length=3)
    description: str | None = None

class PaymentReadDTO(BaseModel):
    id: UUID
    payer_id: UUID
    payee_id: UUID
    src_amount: str
    src_currency: str
    dst_amount: str
    dst_currency: str
    fx_rate: str
    fx_provider: str
    fx_at: str
    status: str
    is_reversal: bool

class FxQuoteDTO(BaseModel):
    base: str
    quote: str
    rate: str
    amount_in: str
    amount_out: str
    provider: str
    as_of: str
