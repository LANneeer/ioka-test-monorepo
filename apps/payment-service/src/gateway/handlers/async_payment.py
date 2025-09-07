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
    uow.payments.save(p)
    await uow.commit()


async def handle_complete(cmd: CompletePayment, uow: AsyncAbstractUnitOfWork, notifier: INotifier | None = None) -> None:
    p = await uow.payments.get_async(cmd.payment_id)
    if not p:
        raise ValueError("Payment not found")
    p.complete()
    uow.payments.save(p)
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
    uow.payments.save(p)
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
    uow.payments.save(p)
    await uow.commit()
    if notifier:
        await notifier.transaction_status(
            tx_id=str(p.id),
            status="refunded",
            amount=f"{p.src_amount} {p.src_currency} → {p.dst_amount} {p.dst_currency} @ {p.fx_rate}",
            from_acc=str(p.payer_id),
            to_acc=str(p.payee_id),
        )

async def on_payment_created(evt: PaymentCreated) -> None: ... # в будущем: обновление баланса

async def on_payment_status_changed(evt: PaymentStatusChanged, uow: AsyncAbstractUnitOfWork) -> None:
    p = await uow.payments.get_async(evt.payment_id)
    if not p:
        return
    try:
        new_status = Status(evt.new_status)
    except ValueError:
        raise ValueError("Status not found")
    p.trasition(new_status)
    uow.payments.add(p)
    await uow.commit()

async def on_payment_refunded(evt: PaymentRefunded, uow: AsyncAbstractUnitOfWork) -> None:
    original = await uow.payments.get_async(evt.payment_id)
    if not original:
        raise ValueError("Payment not found")
    try:
        inv_rate = (Decimal("1") / original.fx_rate).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ZeroDivisionError):
        inv_rate = Decimal("1.0")

    reversal = Payment.create_with_quote(
        payer_id=original.payee_id,
        payee_id=original.payer_id,
        src_amount=original.dst_amount,
        src_currency=original.dst_currency,
        dst_amount=original.src_amount,
        dst_currency=original.src_currency,
        fx_rate=inv_rate,
        fx_provider=original.fx_provider,
        fx_at=original.fx_at,
        description=f"Refund of {original.id}",
    )
    reversal._is_reversal = True

    reversal.mark_processing()
    reversal.complete()

    original._status = Status.REFUNDED
    original._updated_at = datetime.now(timezone.utc)

    uow.payments.save(reversal)
    uow.payments.save(original)
    await uow.commit()
