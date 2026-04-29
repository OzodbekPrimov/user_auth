from dataclasses import dataclass

from django.conf import settings


class GoogleAuthError(Exception):
    """Raised when a Google ID token cannot be trusted."""


class GoogleAuthConfigError(Exception):
    """Raised when Google auth is not configured on the backend."""


@dataclass(frozen=True)
class GoogleUserInfo:
    sub: str
    email: str
    email_verified: bool
    first_name: str = ""
    last_name: str = ""
    picture: str = ""


def verify_google_id_token(raw_id_token: str) -> GoogleUserInfo:
    client_ids = settings.GOOGLE_AUTH.get("CLIENT_IDS", [])
    if not client_ids:
        raise GoogleAuthConfigError("Google client ID sozlanmagan.")

    try:
        from google.auth.transport import requests
        from google.oauth2 import id_token
    except ImportError as exc:
        raise GoogleAuthConfigError("google-auth paketi o'rnatilmagan.") from exc

    try:
        idinfo = id_token.verify_oauth2_token(
            raw_id_token,
            requests.Request(),
        )
    except ValueError as exc:
        raise GoogleAuthError("Google token yaroqsiz yoki muddati o'tgan.") from exc

    if idinfo.get("aud") not in client_ids:
        raise GoogleAuthError("Google token audience mos emas.")

    if idinfo.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise GoogleAuthError("Google token issuer mos emas.")

    sub = idinfo.get("sub")
    email = idinfo.get("email")
    if not sub or not email:
        raise GoogleAuthError("Google token ichida kerakli user ma'lumotlari yo'q.")

    return GoogleUserInfo(
        sub=sub,
        email=email.lower(),
        email_verified=bool(idinfo.get("email_verified")),
        first_name=idinfo.get("given_name", ""),
        last_name=idinfo.get("family_name", ""),
        picture=idinfo.get("picture", ""),
    )
