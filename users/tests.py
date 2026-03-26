from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class UserApiTests(APITestCase):
    def test_create_user_and_get_profile(self):
        payload = {
            "email": "reader@example.com",
            "password": "strongpass123",
            "first_name": "Reader",
            "last_name": "One",
        }
        response = self.client.post(reverse("users:create"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=payload["email"]).exists())

        token_response = self.client.post(
            reverse("users:token"),
            {"email": payload["email"], "password": payload["password"]},
        )
        access_token = token_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZE=f"Bearer {access_token}")
        profile_response = self.client.get(reverse("users:me"))

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["email"], payload["email"])
