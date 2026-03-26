from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from borrowings.models import Borrowing
from payments.services import create_fine_for_borrowing


def process_borrowing_return(borrowing: Borrowing) -> Borrowing:
    with transaction.atomic():
        borrowing = Borrowing.objects.select_for_update().select_related("book").get(
            pk=borrowing.pk
        )
        if borrowing.actual_return_date:
            raise serializers.ValidationError("This borrowing has already been returned.")

        borrowing.actual_return_date = timezone.localdate()
        borrowing.save(update_fields=["actual_return_date"])

        borrowing.book.inventory += 1
        borrowing.book.save(update_fields=["inventory"])

        if borrowing.actual_return_date > borrowing.expected_return_date:
            create_fine_for_borrowing(borrowing)

    return borrowing
