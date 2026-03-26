from decimal import Decimal
from uuid import uuid4

import stripe
from django.conf import settings
from django.db import transaction

from borrowings.tasks import send_payment_success_notification
from payments.models import Payment


def _normalized_success_url() -> str:
    success_url = settings.STRIPE_SUCCESS_URL
    placeholder = "{CHECKOUT_SESSION_ID}"
    if placeholder not in success_url:
        separator = "&" if "?" in success_url else "?"
        success_url = f"{success_url}{separator}session_id={placeholder}"
    return success_url


def _build_session_payload(name: str, amount: Decimal, borrowing_id: int, payment_type: str):
    if settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            success_url=_normalized_success_url(),
            cancel_url=settings.STRIPE_CANCEL_URL,
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": name},
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "borrowing_id": borrowing_id,
                "payment_type": payment_type,
            },
        )
        return {"session_id": session.id, "session_url": session.url}

    mock_session_id = f"mock_session_{uuid4().hex}"
    return {
        "session_id": mock_session_id,
        "session_url": f"{settings.APP_HOST}/api/payments/success/?session_id={mock_session_id}",
    }


def _borrowing_days(borrowing) -> int:
    return max((borrowing.expected_return_date - borrowing.borrow_date).days, 1)


def create_payment_for_borrowing(borrowing) -> Payment:
    amount = borrowing.book.daily_fee * Decimal(_borrowing_days(borrowing))
    session = _build_session_payload(
        name=f"Borrowing payment for {borrowing.book.title}",
        amount=amount,
        borrowing_id=borrowing.id,
        payment_type=Payment.TypeChoices.PAYMENT,
    )
    return Payment.objects.create(
        borrowing=borrowing,
        type=Payment.TypeChoices.PAYMENT,
        money_to_pay=amount,
        session_id=session["session_id"],
        session_url=session["session_url"],
    )


def create_fine_for_borrowing(borrowing) -> Payment | None:
    overdue_days = (borrowing.actual_return_date - borrowing.expected_return_date).days
    if overdue_days <= 0:
        return None

    amount = borrowing.book.daily_fee * Decimal(overdue_days) * settings.FINE_MULTIPLIER
    session = _build_session_payload(
        name=f"Fine payment for {borrowing.book.title}",
        amount=amount,
        borrowing_id=borrowing.id,
        payment_type=Payment.TypeChoices.FINE,
    )
    return Payment.objects.create(
        borrowing=borrowing,
        type=Payment.TypeChoices.FINE,
        money_to_pay=amount,
        session_id=session["session_id"],
        session_url=session["session_url"],
    )


def _is_payment_confirmed(payment: Payment) -> bool:
    if not settings.STRIPE_SECRET_KEY or payment.session_id.startswith("mock_session_"):
        return True

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(payment.session_id)
    return session.payment_status == "paid"


def mark_payment_as_paid(payment: Payment) -> Payment:
    if payment.status == Payment.StatusChoices.PAID:
        return payment

    if not _is_payment_confirmed(payment):
        return payment

    with transaction.atomic():
        payment.status = Payment.StatusChoices.PAID
        payment.save(update_fields=["status"])
        transaction.on_commit(
            lambda payment_id=payment.id: send_payment_success_notification.delay(payment_id)
        )

    return payment
