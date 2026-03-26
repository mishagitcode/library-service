from celery import shared_task
from django.utils import timezone

from borrowings.models import Borrowing
from config.telegram import send_telegram_message
from payments.models import Payment


@shared_task
def send_borrowing_created_notification(borrowing_id: int) -> bool:
    borrowing = Borrowing.objects.select_related("book", "user").get(pk=borrowing_id)
    message = (
        "New borrowing created:\n"
        f"Borrowing ID: {borrowing.id}\n"
        f"User: {borrowing.user.email}\n"
        f"Book: {borrowing.book.title}\n"
        f"Borrow date: {borrowing.borrow_date}\n"
        f"Expected return: {borrowing.expected_return_date}"
    )
    return send_telegram_message(message)


@shared_task
def send_payment_success_notification(payment_id: int) -> bool:
    payment = Payment.objects.select_related("borrowing", "borrowing__book", "borrowing__user").get(
        pk=payment_id
    )
    message = (
        "Payment completed:\n"
        f"Payment ID: {payment.id}\n"
        f"Type: {payment.type}\n"
        f"User: {payment.borrowing.user.email}\n"
        f"Book: {payment.borrowing.book.title}\n"
        f"Amount: ${payment.money_to_pay}"
    )
    return send_telegram_message(message)


@shared_task
def notify_overdue_borrowings() -> int:
    today = timezone.localdate()
    overdue_borrowings = Borrowing.objects.select_related("book", "user").filter(
        expected_return_date__lte=today,
        actual_return_date__isnull=True,
    )

    if not overdue_borrowings.exists():
        send_telegram_message("No borrowings overdue today!")
        return 0

    for borrowing in overdue_borrowings:
        message = (
            "Overdue borrowing detected:\n"
            f"Borrowing ID: {borrowing.id}\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )
        send_telegram_message(message)

    return overdue_borrowings.count()
