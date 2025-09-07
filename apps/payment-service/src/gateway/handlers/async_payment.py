from decimal import Decimal
from uuid import UUID

from patterns.unit_of_work import AsyncAbstractUnitOfWork

from src.domains.payments.model import Payment
from src.dto.commands import (
    CreatePayment,
    MarkProcessing,
    CompletePayment,
    FailPayment,
    RefundPayment,
    PaymentCreated,
    PaymentStatusChanged,
    PaymentRefunded,
)
from src.domains.payments.abstraction import (
    IUsersClient,
    IFxClient,
    INotifier,
)


async def handle_create_payment(
    cmd: CreatePayment,
    uow: AsyncAbstractUnitOfWork,
    users: IUsersClient,
    fx: IFxClient,
    notifier: INotifier | None = None,
) -> UUID:
    if not await users.user_exists(cmd.payer_id):
        raise ValueError("Payer not found")
    if not await users.user_exists(cmd.payee_id):
        raise ValueError("Payee not found")

    src_amount = Decimal(cmd.src_amount)
    quote = await fx.convert(base=cmd.src_currency, quote=cmd.dst_currency, amount=src_amount)

    payment = Payment.create_with_quote(
        payer_id=cmd.payer_id,
        payee_id=cmd.payee_id,
        src_amount=src_amount,
        src_currency=cmd.src_currency,
        dst_amount=quote.amount_out,
        dst_currency=cmd.dst_currency,
        fx_rate=quote.rate,
        fx_provider=quote.provider,
        fx_at=quote.as_of,
        description=cmd.description,
    )

    uow.payments.add(payment)
    await uow.commit()

    if notifier:
        await notifier.transaction_status(
            tx_id=str(payment.id),
            status="created",
            amount=f"{payment.src_amount} {payment.src_currency} → {payment.dst_amount} {payment.dst_currency} @ {payment.fx_rate}",
            from_acc=str(payment.payer_id),
            to_acc=str(payment.payee_id),
        )

    return payment.id


async def handle_mark_processing(cmd: MarkProcessing, uow: AsyncAbstractUnitOfWork) -> None:
    p = await uow.payments.get_async(cmd.payment_id)
    if not p:
        raise ValueError("Payment not found")
    p.mark_processing()
    uow.payments.add(p)
    await uow.commit()


async def handle_complete(cmd: CompletePayment, uow: AsyncAbstractUnitOfWork, notifier: INotifier | None = None) -> None:
    p = await uow.payments.get_async(cmd.payment_id)
    if not p:
        raise ValueError("Payment not found")
    p.complete()
    uow.payments.add(p)
    await uow.commit()
    if notifier:
        await notifier.transaction_status(
            tx_id=str(p.id),
            status="completed",
            amount=f"{p.src_amount} {p.src_currency} → {p.dst_amount} {p.dst_currency} @ {p.fx_rate}",
            from_acc=str(p.payer_id),
            to_acc=str(p.payee_id),
        )


async def handle_fail(cmd: FailPayment, uow: AsyncAbstractUnitOfWork, notifier: INotifier | None = None) -> None:
    p = await uow.payments.get_async(cmd.payment_id)
    if not p:
        raise ValueError("Payment not found")
    p.fail()
    uow.payments.add(p)
    await uow.commit()
    if notifier:
        await notifier.transaction_status(
            tx_id=str(p.id),
            status="failed",
            amount=f"{p.src_amount} {p.src_currency} → {p.dst_amount} {p.dst_currency} @ {p.fx_rate}",
            from_acc=str(p.payer_id),
            to_acc=str(p.payee_id),
        )


async def handle_refund(cmd: RefundPayment, uow: AsyncAbstractUnitOfWork, notifier: INotifier | None = None) -> None:
    p = await uow.payments.get_async(cmd.payment_id)
    if not p:
        raise ValueError("Payment not found")
    p.refund(original_payment_id=cmd.original_payment_id)
    uow.payments.add(p)
    await uow.commit()
    if notifier:
        await notifier.transaction_status(
            tx_id=str(p.id),
            status="refunded",
            amount=f"{p.src_amount} {p.src_currency} → {p.dst_amount} {p.dst_currency} @ {p.fx_rate}",
            from_acc=str(p.payer_id),
            to_acc=str(p.payee_id),
        )

async def on_payment_created(evt: PaymentCreated) -> None: ...
async def on_payment_status_changed(evt: PaymentStatusChanged) -> None: ...
async def on_payment_refunded(evt: PaymentRefunded) -> None: ...
