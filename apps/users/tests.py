import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
)
class EmailChangeAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="+998901234567")
        self.client.force_authenticate(self.user)
        self.request_url = reverse("profile-email-request")
        self.verify_url = reverse("profile-email-verify")

    def test_email_change_requires_code_confirmation(self):
        response = self.client.post(
            self.request_url,
            {"email": "New@Example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

        self.user.refresh_from_db()
        self.assertIsNone(self.user.email)

        code = re.search(r"\b\d{6}\b", mail.outbox[0].body).group(0)
        response = self.client.post(
            self.verify_url,
            {"email": "new@example.com", "code": code},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")

    def test_profile_patch_does_not_update_email_directly(self):
        response = self.client.patch(
            reverse("user-profile"),
            {"email": "new@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.email)

    def test_email_change_rejects_existing_email_case_insensitive(self):
        User.objects.create_user(email="taken@example.com")

        response = self.client.post(
            self.request_url,
            {"email": "Taken@Example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(mail.outbox), 0)
