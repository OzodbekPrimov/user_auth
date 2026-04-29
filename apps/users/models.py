import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager
from .validators import validate_phone, validate_email_domain


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User — phone/email orqali auth, username yo'q."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ─── Identifiers ───
    phone = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="format: +998901234567",
        validators=[validate_phone],
    )
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        validators=[validate_email_domain],
    )

    # ─── Profile ───
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        null=True,
        blank=True
    )
    country = models.CharField(
        max_length=50,
        blank=True,
        help_text="Masalan Uzbekistan, Tashkent"
    )

    # ─── Status ───
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # ─── Timestamps ───
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='custom_users',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='custom_users',
    )

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["email"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                        models.Q(phone__isnull=False) |
                        models.Q(email__isnull=False)
                ),
                name="user_must_have_phone_or_email"
            )
        ]

    def __str__(self):
        return self.get_display_name()

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_display_name(self) -> str:
        return (
                self.full_name
                or self.email
                or self.phone
                or str(self.id)
        )