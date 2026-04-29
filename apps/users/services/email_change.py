import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.users.models import EmailChangeRequest

User = get_user_model()

CODE_LENGTH = 6
EXPIRY_MINUTES = 10
MAX_ATTEMPTS = 5
RATE_LIMIT_COUNT = 3
RATE_LIMIT_WINDOW_MINUTES = 10


class EmailDeliveryError(Exception):
    pass


class EmailChangeRateLimitError(Exception):
    pass


def normalize_email(email: str) -> str:
    return User.objects.normalize_email(email).lower()


def ensure_email_can_be_used(user, email: str) -> None:
    if user.email and user.email.lower() == email:
        raise serializers.ValidationError({"email": "Bu email profilingizda allaqachon mavjud."})

    if User.objects.exclude(pk=user.pk).filter(email__iexact=email).exists():
        raise serializers.ValidationError({"email": "Bu email allaqachon band."})


def _generate_code() -> str:
    upper_bound = 10 ** CODE_LENGTH
    return f"{secrets.randbelow(upper_bound):0{CODE_LENGTH}d}"


def _ensure_not_rate_limited(user, email: str) -> None:
    window = timezone.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    count = EmailChangeRequest.objects.filter(
        user=user,
        email=email,
        created_at__gte=window,
    ).count()

    if count >= RATE_LIMIT_COUNT:
        raise EmailChangeRateLimitError("Juda ko'p kod so'rovi. Keyinroq urinib ko'ring.")


def request_email_change(user, email: str) -> EmailChangeRequest:
    email = normalize_email(email)
    ensure_email_can_be_used(user, email)
    _ensure_not_rate_limited(user, email)

    code = _generate_code()
    now = timezone.now()

    with transaction.atomic():
        EmailChangeRequest.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=now,
        ).update(is_used=True, used_at=now)

        request = EmailChangeRequest.objects.create(
            user=user,
            email=email,
            code_hash=make_password(code),
            expires_at=now + timedelta(minutes=EXPIRY_MINUTES),
        )

    try:
        send_mail(
            subject="Emailni tasdiqlash kodi",
            message=(
                f"Emailni yangilash uchun tasdiqlash kodingiz: {code}\n\n"
                f"Kod {EXPIRY_MINUTES} daqiqa amal qiladi."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as exc:
        EmailChangeRequest.objects.filter(pk=request.pk).update(
            is_used=True,
            used_at=timezone.now(),
        )
        raise EmailDeliveryError("Email yuborib bo'lmadi.") from exc

    return request


def confirm_email_change(user, email: str, code: str) -> str:
    email = normalize_email(email)
    now = timezone.now()

    with transaction.atomic():
        request = (
            EmailChangeRequest.objects
            .select_for_update()
            .filter(
                user=user,
                email=email,
                is_used=False,
                expires_at__gt=now,
            )
            .order_by("-created_at")
            .first()
        )

        if not request:
            raise serializers.ValidationError(
                {"detail": "Kod topilmadi yoki muddati o'tgan."}
            )

        request.attempts += 1

        if not check_password(code, request.code_hash):
            if request.attempts >= MAX_ATTEMPTS:
                request.is_used = True
                request.used_at = now
                request.save(update_fields=["attempts", "is_used", "used_at"])
                raise serializers.ValidationError(
                    {"detail": "Juda ko'p noto'g'ri urinish. Yangi kod so'rang."}
                )

            request.save(update_fields=["attempts"])
            raise serializers.ValidationError({"code": "Kod noto'g'ri."})

        ensure_email_can_be_used(user, email)

        user.email = email
        user.save(update_fields=["email", "updated_at"])

        request.is_used = True
        request.used_at = now
        request.save(update_fields=["attempts", "is_used", "used_at"])

    return email
