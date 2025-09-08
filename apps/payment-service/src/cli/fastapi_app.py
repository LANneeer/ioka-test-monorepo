import logging
from logstash_async.handler import AsynchronousLogstashHandler
from logstash_async.formatter import LogstashFormatter
from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, status, Query, Request, Response
from src.bootstrap.async_settings import bootstrap_async
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.infrastructure.hooks import PromAuditHook
from src.infrastructure.middleware import IdempotencyMiddleware, MetricsMiddleware, prom_endpoint
from src.cli.error import install_exception_handlers
from src.config import settings
from decimal import Decimal

from src.dto.commands import CreatePayment, CompletePayment, FailPayment, RefundPayment, MarkProcessing
from src.gateway.schemas.payments import PaymentCreateDTO, PaymentReadDTO, FxQuoteDTO
from src.infrastructure.clients import UsersClient, FxClient

logstash_handler = AsynchronousLogstashHandler(
    host=settings.LOGSTASH_HOST,
    port=settings.LOGSTASH_PORT,
    database_path=None
)
logstash_handler.setFormatter(LogstashFormatter())

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    handlers=[logging.StreamHandler(), logstash_handler],
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Payment Service (async with FX)",
    servers=[{"url": "/api/payments"}],
)

app.add_middleware(IdempotencyMiddleware)
if settings.PROM_ENABLED:
    app.add_middleware(MetricsMiddleware)
install_exception_handlers(app)
users_client = UsersClient()
fx_client = FxClient()

async def get_uow():
    async with AsyncUnitOfWork() as uow:
        yield uow

@app.get("/metrics")
def metrics():
    data, content_type = prom_endpoint()
    return Response(content=data, media_type=content_type)

@app.get("/fx/quote", response_model=FxQuoteDTO)
async def fx_quote(base: str, quote: str, amount: str):
    q = await fx_client.convert(base=base, quote=quote, amount=Decimal(amount))
    return FxQuoteDTO(
        base=q.base, quote=q.quote, rate=str(q.rate),
        amount_in=str(q.amount_in), amount_out=str(q.amount_out),
        provider=q.provider, as_of=q.as_of.isoformat()
    )

@app.post("/payments", response_model=PaymentReadDTO, status_code=status.HTTP_201_CREATED)
async def create_payment(
    dto: PaymentCreateDTO,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook, fx=fx_client, users=users_client)
    [payment_id] = await bus.handle(CreatePayment(
        payer_id=dto.payer_id,
        payee_id=dto.payee_id,
        src_amount=dto.src_amount,
        src_currency=dto.src_currency,
        dst_currency=dto.dst_currency,
        description=dto.description,
    ))
    p = await uow.payments.get_async(payment_id)
    if not p: raise HTTPException(500, "Payment not persisted")
    return PaymentReadDTO(
        id=p.id, payer_id=p.payer_id, payee_id=p.payee_id,
        src_amount=str(p.src_amount), src_currency=p.src_currency,
        dst_amount=str(p.dst_amount), dst_currency=p.dst_currency,
        fx_rate=str(p.fx_rate), fx_provider=p.fx_provider, fx_at=p.fx_at.isoformat(),
        status=p.status.value, is_reversal=p.is_reversal,
    )


@app.get("/payments/{payment_id}", response_model=PaymentReadDTO)
async def get_payment(payment_id: UUID, uow: Annotated[AsyncUnitOfWork, Depends(get_uow)]):
    p = await uow.payments.get_async(payment_id)
    if not p: raise HTTPException(404, "Payment not found")
    return PaymentReadDTO(
            id=p.id,
            payer_id=p.payer_id,
            payee_id=p.payee_id,
            src_amount=str(p.src_amount),
            src_currency=p.src_currency,
            dst_amount=str(p.dst_amount),
            dst_currency=p.dst_currency,
            fx_rate=str(p.fx_rate),
            fx_provider=p.fx_provider,
            fx_at=p.fx_at.isoformat(),
            status=p.status.value,
            is_reversal=p.is_reversal,
        )


@app.get("/payments", response_model=list[PaymentReadDTO])
async def list_payments(
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
    payer_id: UUID | None = Query(None),
    payee_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items = await uow.payments.list_payments(payer_id=payer_id, payee_id=payee_id, skip=skip, limit=limit)
    return [
        PaymentReadDTO(
            id=p.id,
            payer_id=p.payer_id,
            payee_id=p.payee_id,
            src_amount=str(p.src_amount),
            src_currency=p.src_currency,
            dst_amount=str(p.dst_amount),
            dst_currency=p.dst_currency,
            fx_rate=str(p.fx_rate),
            fx_provider=p.fx_provider,
            fx_at=p.fx_at.isoformat(),
            status=p.status.value,
            is_reversal=p.is_reversal,
        )
        for p in items
    ]

@app.post("/payments/{payment_id}/processing", status_code=204)
async def mark_processing(payment_id: UUID, uow: Annotated[AsyncUnitOfWork, Depends(get_uow)]):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook)
    await bus.handle(MarkProcessing(payment_id=payment_id))
    return Response(status_code=204)

@app.post("/payments/{payment_id}/complete", status_code=204)
async def complete_payment(payment_id: UUID, uow: Annotated[AsyncUnitOfWork, Depends(get_uow)]):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook)
    await bus.handle(CompletePayment(payment_id=payment_id))
    return Response(status_code=204)

@app.post("/payments/{payment_id}/fail", status_code=204)
async def fail_payment(payment_id: UUID, uow: Annotated[AsyncUnitOfWork, Depends(get_uow)]):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook)
    await bus.handle(FailPayment(payment_id=payment_id))
    return Response(status_code=204)

@app.post("/payments/{payment_id}/refund", status_code=204)
async def refund_payment(payment_id: UUID, original_payment_id: UUID, uow: Annotated[AsyncUnitOfWork, Depends(get_uow)]):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook)
    await bus.handle(RefundPayment(payment_id=payment_id, original_payment_id=original_payment_id))
    return Response(status_code=204)
