import random
import string
from datetime import timedelta

from django.utils import timezone

from apps.auth.models import OTPCode

OTP_EXPIRY_MINUTES = 2
MAX_ATTEMPTS = 5
RATE_LIMIT_COUNT = 3
RATE_LIMIT_WINDOW_MINUTES = 5


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=4))


def is_rate_limited(phone: str) -> bool:
    window = timezone.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    return OTPCode.objects.filter(phone=phone, created_at__gte=window).count() >= RATE_LIMIT_COUNT


def create_otp(phone: str) -> OTPCode:
    return OTPCode.objects.create(
        phone=phone,
        code=_generate_code(),
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )



def verify_otp(phone: str, code: str) -> tuple[bool, str]:
    otp = (
        OTPCode.objects
        .filter(phone=phone, is_used=False, expires_at__gt=timezone.now())
        .order_by("-created_at")
        .first()
    )

    if not otp:
        return False, "Kod topilmadi yoki muddati o'tgan."

    otp.attempts += 1

    if otp.code == code:
        otp.is_used = True
        otp.save(update_fields=["attempts", "is_used"])
        return True, "OK"

    if otp.attempts >= MAX_ATTEMPTS:
        otp.is_used = True
        otp.save(update_fields=["attempts", "is_used"])
        return False, "Juda ko'p noto'g'ri urinish. Yangi kod so'rang."

    otp.save(update_fields=["attempts"])
    return False, "Kod noto'g'ri."
