from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.auth.models import AuthProvider, OTPCode
from apps.auth.services.google import GoogleAuthError, GoogleUserInfo
from apps.auth.services.otp import MAX_ATTEMPTS, verify_otp

User = get_user_model()


class GoogleAuthAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("google-auth")

    @patch("apps.auth.views.google.verify_google_id_token")
    def test_google_auth_creates_user_and_provider(self, verify_google_id_token):
        verify_google_id_token.return_value = GoogleUserInfo(
            sub="google-sub-1",
            email="ali@example.com",
            email_verified=True,
            first_name="Ali",
            last_name="Valiyev",
        )

        response = self.client.post(self.url, {"id_token": "valid-token"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["is_new_user"])

        user = User.objects.get(email="ali@example.com")
        self.assertEqual(user.first_name, "Ali")
        self.assertTrue(
            AuthProvider.objects.filter(
                user=user,
                provider_type=AuthProvider.ProviderType.GOOGLE,
                provider_uid="google-sub-1",
            ).exists()
        )

    @patch("apps.auth.views.google.verify_google_id_token")
    def test_google_auth_uses_existing_provider(self, verify_google_id_token):
        user = User.objects.create_user(email="ali@example.com")
        AuthProvider.objects.create(
            user=user,
            provider_type=AuthProvider.ProviderType.GOOGLE,
            provider_uid="google-sub-1",
        )
        verify_google_id_token.return_value = GoogleUserInfo(
            sub="google-sub-1",
            email="changed@example.com",
            email_verified=True,
        )

        response = self.client.post(self.url, {"id_token": "valid-token"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_new_user"])
        self.assertEqual(User.objects.count(), 1)

    @patch("apps.auth.views.google.verify_google_id_token")
    def test_google_auth_rejects_unverified_email(self, verify_google_id_token):
        verify_google_id_token.return_value = GoogleUserInfo(
            sub="google-sub-1",
            email="ali@example.com",
            email_verified=False,
        )

        response = self.client.post(self.url, {"id_token": "valid-token"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.count(), 0)

    @patch("apps.auth.views.google.verify_google_id_token")
    def test_google_auth_rejects_invalid_token(self, verify_google_id_token):
        verify_google_id_token.side_effect = GoogleAuthError("Google token yaroqsiz.")

        response = self.client.post(self.url, {"id_token": "invalid-token"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OTPVerificationTests(APITestCase):
    def test_correct_code_on_last_attempt_is_accepted(self):
        otp = OTPCode.objects.create(
            phone="+998901234567",
            code="1234",
            expires_at=timezone.now() + timedelta(minutes=2),
            attempts=MAX_ATTEMPTS - 1,
        )

        ok, message = verify_otp("+998901234567", "1234")

        otp.refresh_from_db()
        self.assertTrue(ok)
        self.assertEqual(message, "OK")
        self.assertTrue(otp.is_used)
        self.assertEqual(otp.attempts, MAX_ATTEMPTS)

    def test_wrong_code_on_last_attempt_blocks_otp(self):
        otp = OTPCode.objects.create(
            phone="+998901234567",
            code="1234",
            expires_at=timezone.now() + timedelta(minutes=2),
            attempts=MAX_ATTEMPTS - 1,
        )

        ok, message = verify_otp("+998901234567", "0000")

        otp.refresh_from_db()
        self.assertFalse(ok)
        self.assertEqual(message, "Juda ko'p noto'g'ri urinish. Yangi kod so'rang.")
        self.assertTrue(otp.is_used)
        self.assertEqual(otp.attempts, MAX_ATTEMPTS)
