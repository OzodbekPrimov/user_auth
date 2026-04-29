from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth.models import AuthProvider
from apps.auth.serializers import GoogleAuthSerializer, TokenResponseSerializer
from apps.auth.services.google import GoogleAuthConfigError, GoogleAuthError, verify_google_id_token
from apps.auth.views.utils import issue_tokens_for_user

User = get_user_model()


@extend_schema(tags=["Google Auth"])
class GoogleAuthAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Google orqali kirish",
        description=(
            "Clientdan kelgan Google ID tokenni tekshiradi. Token haqiqiy bo'lsa "
            "mavjud userga kiradi yoki yangi user yaratib JWT access/refresh qaytaradi."
        ),
        request=GoogleAuthSerializer,
        responses={
            200: TokenResponseSerializer,
            401: OpenApiResponse(description="Google token yaroqsiz yoki muddati o'tgan"),
            403: OpenApiResponse(description="Google email tasdiqlanmagan yoki user faol emas"),
            409: OpenApiResponse(description="Email boshqa Google akkauntga ulangan"),
            503: OpenApiResponse(description="Google auth sozlanmagan"),
        },
        examples=[
            OpenApiExample("So'rov", value={"id_token": "eyJ..."}, request_only=True),
            OpenApiExample(
                "Javob",
                value={"access": "eyJ...", "refresh": "eyJ...", "is_new_user": True},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            google_user = verify_google_id_token(serializer.validated_data["id_token"])
        except GoogleAuthConfigError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except GoogleAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        if not google_user.email_verified:
            return Response(
                {"detail": "Google email tasdiqlanmagan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            provider = (
                AuthProvider.objects
                .select_related("user")
                .filter(
                    provider_type=AuthProvider.ProviderType.GOOGLE,
                    provider_uid=google_user.sub,
                )
                .first()
            )

            if provider:
                user = provider.user
                is_new_user = False
            else:
                user = User.objects.filter(email=google_user.email).first()
                is_new_user = user is None

                if user is None:
                    user = User.objects.create_user(
                        email=google_user.email,
                        first_name=google_user.first_name,
                        last_name=google_user.last_name,
                        is_active=True,
                    )
                elif AuthProvider.objects.filter(
                    user=user,
                    provider_type=AuthProvider.ProviderType.GOOGLE,
                ).exists():
                    return Response(
                        {"detail": "Bu email boshqa Google akkauntga ulangan."},
                        status=status.HTTP_409_CONFLICT,
                    )

                AuthProvider.objects.create(
                    user=user,
                    provider_type=AuthProvider.ProviderType.GOOGLE,
                    provider_uid=google_user.sub,
                )

            if not user.is_active:
                return Response(
                    {"detail": "Foydalanuvchi faol emas."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        tokens = issue_tokens_for_user(user)
        return Response({**tokens, "is_new_user": is_new_user})
