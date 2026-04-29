import uuid

from django.conf import settings
from django.db import models


class AuthProvider(models.Model):
    """Userga ulangan auth provayderlar (phone, google, apple)."""

    class ProviderType(models.TextChoices):
        PHONE = "phone", "Phone"
        GOOGLE = "google", "Google"
        APPLE = "apple", "Apple"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_providers",
    )
    provider_type = models.CharField(
        max_length=20,
        choices=ProviderType.choices,
    )
    provider_uid = models.CharField(
        max_length=255,
        help_text="Google sub, Apple sub, yoki phone number",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_providers"
        constraints = [
            models.UniqueConstraint(
                fields=["provider_type", "provider_uid"],
                name="unique_provider_uid",
            ),
            models.UniqueConstraint(
                fields=["user", "provider_type"],
                name="unique_user_provider_type",
            ),
        ]
        indexes = [
            models.Index(fields=["provider_type", "provider_uid"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.provider_type}"


class OTPCode(models.Model):
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "otp_codes"
        indexes = [
            models.Index(fields=["phone", "is_used", "expires_at"]),
        ]

    def __str__(self):
        return f"OTP({self.phone})"
