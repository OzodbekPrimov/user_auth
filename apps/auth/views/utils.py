from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens_for_user(user):
    update_last_login(None, user)
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
