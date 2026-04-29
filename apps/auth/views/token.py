from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from apps.auth.serializers import TokenRefreshResponseSerializer


@extend_schema(tags=["Phone Auth"])
class RefreshAccessTokenView(TokenRefreshView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Access tokenni yangilash",
        description=(
            "Refresh token orqali yangi access token qaytaradi. "
            "Token rotation yoqilganligi sababli javobda yangi refresh token ham keladi, "
            "eski refresh token esa blacklist qilinadi."
        ),
        request=TokenRefreshSerializer,
        responses={
            200: TokenRefreshResponseSerializer,
            401: OpenApiResponse(description="Refresh token yaroqsiz, muddati o'tgan yoki blacklist qilingan"),
        },
        examples=[
            OpenApiExample("So'rov", value={"refresh": "eyJ..."}, request_only=True),
            OpenApiExample("Javob", value={"access": "eyJ...", "refresh": "eyJ..."}, response_only=True),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
