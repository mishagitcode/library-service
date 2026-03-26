from rest_framework import serializers

from payments.models import Payment


class PaymentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "status", "type", "session_url", "money_to_pay")


class PaymentSerializer(serializers.ModelSerializer):
    borrowing_id = serializers.IntegerField(source="borrowing.id", read_only=True)
    book_title = serializers.CharField(source="borrowing.book.title", read_only=True)
    user_id = serializers.IntegerField(source="borrowing.user.id", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing_id",
            "user_id",
            "book_title",
            "session_url",
            "session_id",
            "money_to_pay",
        )
