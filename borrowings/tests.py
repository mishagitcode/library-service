from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from users.models import User


class BorrowingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="userpass123",
        )
        self.book = Book.objects.create(
            title="1984",
            author="George Orwell",
            cover=Book.CoverChoices.HARD,
            inventory=2,
            daily_fee=Decimal("3.00"),
        )
        self.client.force_authenticate(self.user)

    def test_create_borrowing_decreases_inventory_and_creates_payment(self):
        payload = {
            "book": self.book.id,
            "expected_return_date": str(timezone.localdate() + timedelta(days=3)),
        }

        response = self.client.post(reverse("borrowings:borrowings-list"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        borrowing = Borrowing.objects.get()
        payment = Payment.objects.get()

        self.assertEqual(self.book.inventory, 1)
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(payment.borrowing, borrowing)
        self.assertEqual(payment.status, Payment.StatusChoices.PENDING)

    def test_return_borrowing_creates_fine_when_overdue(self):
        borrowing = Borrowing.objects.create(
            borrow_date=timezone.localdate() - timedelta(days=5),
            expected_return_date=timezone.localdate() - timedelta(days=2),
            book=self.book,
            user=self.user,
        )
        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.TypeChoices.PAYMENT,
            session_id="mock_session_existing",
            session_url="http://testserver/api/payments/success/?session_id=mock_session_existing",
            money_to_pay=Decimal("9.00"),
        )
        self.book.inventory = 1
        self.book.save(update_fields=["inventory"])

        response = self.client.post(
            reverse("borrowings:borrowings-return-borrowing", args=[borrowing.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertIsNotNone(borrowing.actual_return_date)
        self.assertEqual(self.book.inventory, 2)
        self.assertEqual(
            borrowing.payments.filter(type=Payment.TypeChoices.FINE).count(),
            1,
        )
