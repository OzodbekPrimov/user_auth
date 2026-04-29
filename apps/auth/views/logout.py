from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth.serializers import LogoutSerializer


@extend_schema(tags=["Phone Auth"])
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Tizimdan chiqish",
        description=(
            "Refresh tokenni SimpleJWT blacklist ro'yxatiga qo'shadi. "
            "Shundan keyin bu refresh token orqali yangi access token olib bo'lmaydi."
        ),
        request=LogoutSerializer,
        responses={
            205: OpenApiResponse(description="Tizimdan muvaffaqiyatli chiqildi"),
            400: OpenApiResponse(description="Yaroqsiz yoki boshqa foydalanuvchiga tegishli token"),
        },
        examples=[
            OpenApiExample("So'rov", value={"refresh": "eyJ..."}, request_only=True),
            OpenApiExample("Javob", value={"detail": "Tizimdan muvaffaqiyatli chiqildi."}, response_only=True),
        ],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(raw_refresh_token)

            if str(token.get("user_id")) != str(request.user.id):
                return Response(
                    {"detail": "Refresh token joriy foydalanuvchiga tegishli emas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token.blacklist()

            return Response(
                {"detail": "Tizimdan muvaffaqiyatli chiqildi."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except TokenError:
            return Response(
                {"detail": "Yaroqsiz token yoki allaqachon blacklist qilingan."},
                status=status.HTTP_400_BAD_REQUEST,
            )
