from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from borrowings.tasks import send_borrowing_created_notification
from payments.serializers import PaymentSummarySerializer
from payments.services import create_payment_for_borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    payments = PaymentSummarySerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user_id",
            "is_active",
            "payments",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date")
        read_only_fields = ("id",)

    def validate_book(self, value):
        if value.inventory < 1:
            raise serializers.ValidationError("Book is out of stock.")
        return value

    def validate_expected_return_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError(
                "Expected return date cannot be earlier than today."
            )
        return value

    def create(self, validated_data):
        request = self.context["request"]
        borrow_date = timezone.localdate()

        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=validated_data["book"].pk)
            if book.inventory < 1:
                raise serializers.ValidationError({"book": "Book is out of stock."})

            book.inventory -= 1
            book.save(update_fields=["inventory"])

            borrowing = Borrowing.objects.create(
                borrow_date=borrow_date,
                expected_return_date=validated_data["expected_return_date"],
                book=book,
                user=request.user,
            )
            create_payment_for_borrowing(borrowing)

            transaction.on_commit(
                lambda borrowing_id=borrowing.id: send_borrowing_created_notification.delay(
                    borrowing_id
                )
            )

        return borrowing
