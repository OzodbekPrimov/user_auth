import re
from django.core.exceptions import ValidationError


_PHONE_RE = re.compile(r'^\+\d{7,15}$')
_COUNTRY_RE = re.compile(r'^[A-Z]{2}$')


def validate_phone(value: str) -> None:
    if not _PHONE_RE.match(value):
        raise ValidationError(
            "Telefon raqam noto'g'ri formatda. To'g'ri format: +998901234567",
            code='invalid_phone',
        )


def validate_email_domain(value: str) -> None:
    blocked = {'mailinator.com', 'tempmail.com', 'guerrillamail.com', 'throwam.com'}
    domain = value.rsplit('@', 1)[-1].lower()
    if domain in blocked:
        raise ValidationError(
            "Bu email domeni qabul qilinmaydi.",
            code='blocked_email_domain',
        )


# def validate_country(value: str) -> None:
#     if value and not _COUNTRY_RE.match(value):
#         raise ValidationError(
#             "Davlat kodi ISO 3166-1 alpha-2 formatida bo'lishi kerak: UZ, RU, KZ",
#             code='invalid_country',
#         )