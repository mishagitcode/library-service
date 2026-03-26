from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from users.models import User


class PaymentApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="ownerpass123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123",
        )
        book = Book.objects.create(
            title="Clean Code",
            author="Robert C. Martin",
            cover=Book.CoverChoices.SOFT,
            inventory=4,
            daily_fee=Decimal("4.00"),
        )
        self.borrowing = Borrowing.objects.create(
            borrow_date="2026-03-20",
            expected_return_date="2026-03-23",
            book=book,
            user=self.owner,
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            type=Payment.TypeChoices.PAYMENT,
            session_id="mock_session_test",
            session_url="http://testserver/api/payments/success/?session_id=mock_session_test",
            money_to_pay=Decimal("12.00"),
        )

    def test_user_sees_only_own_payments(self):
        other_borrowing = Borrowing.objects.create(
            borrow_date="2026-03-20",
            expected_return_date="2026-03-21",
            book=self.borrowing.book,
            user=self.other_user,
        )
        Payment.objects.create(
            borrowing=other_borrowing,
            type=Payment.TypeChoices.PAYMENT,
            session_id="mock_session_other",
            session_url="http://testserver/api/payments/success/?session_id=mock_session_other",
            money_to_pay=Decimal("4.00"),
        )

        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse("payments:list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.payment.id)

    def test_success_endpoint_marks_payment_as_paid(self):
        response = self.client.get(
            reverse("payments:success"),
            {"session_id": self.payment.session_id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.StatusChoices.PAID)
