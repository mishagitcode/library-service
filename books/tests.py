from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from users.models import User


class BookApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="userpass123",
        )

    def test_books_list_is_public(self):
        Book.objects.create(
            title="Dune",
            author="Frank Herbert",
            cover=Book.CoverChoices.HARD,
            inventory=3,
            daily_fee=Decimal("1.50"),
        )

        response = self.client.get(reverse("books:books-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_only_admin_can_create_book(self):
        payload = {
            "title": "Foundation",
            "author": "Isaac Asimov",
            "cover": Book.CoverChoices.SOFT,
            "inventory": 5,
            "daily_fee": "2.25",
        }

        self.client.force_authenticate(self.user)
        forbidden_response = self.client.post(reverse("books:books-list"), payload)
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        allowed_response = self.client.post(reverse("books:books-list"), payload)
        self.assertEqual(allowed_response.status_code, status.HTTP_201_CREATED)
