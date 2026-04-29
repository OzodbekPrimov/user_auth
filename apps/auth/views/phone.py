from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth.models import AuthProvider
from apps.auth.serializers import PhoneRequestSerializer, PhoneVerifySerializer, TokenResponseSerializer
from apps.auth.services.otp import create_otp, is_rate_limited, verify_otp
from apps.auth.services.telegram import send_otp
from apps.auth.views.utils import issue_tokens_for_user

User = get_user_model()


@extend_schema(tags=["Phone Auth"])
class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="OTP kod so'rash",
        description="Telefon raqamga 4 xonali OTP kod yuboradi (admin Telegram ga keladi). 5 daqiqada max 3 ta so'rov.",
        request=PhoneRequestSerializer,
        responses={
            200: OpenApiResponse(description="Kod yuborildi"),
            429: OpenApiResponse(description="Rate limit — juda ko'p so'rov"),
            503: OpenApiResponse(description="Telegram xizmati ishlamayapti"),
        },
        examples=[
            OpenApiExample("So'rov", value={"phone": "+998901234567"}, request_only=True),
            OpenApiExample("Javob", value={"detail": "Kod adminga yuborildi. 2 daqiqa ichida kiriting."}, response_only=True),
        ],
    )
    def post(self, request):
        serializer = PhoneRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        if is_rate_limited(phone):
            return Response(
                {"detail": "Juda ko'p so'rov. 5 daqiqadan keyin urinib ko'ring."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp = create_otp(phone)

        try:
            send_otp(phone, otp.code)
        except Exception:
            otp.delete()
            return Response(
                {"detail": "Kod yuborishda xatolik. Keyinroq urinib ko'ring."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"detail": "Kod adminga yuborildi. 2 daqiqa ichida kiriting."})


@extend_schema(tags=["Phone Auth"])
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="OTP kodni tasdiqlash",
        description="Telefon raqam va kodni tekshiradi. To'g'ri bo'lsa JWT access/refresh tokenlar qaytaradi. 5 noto'g'ri urinishdan keyin kod bloklanadi.",
        request=PhoneVerifySerializer,
        responses={
            200: TokenResponseSerializer,
            400: OpenApiResponse(description="Noto'g'ri kod yoki muddati o'tgan"),
        },
        examples=[
            OpenApiExample("So'rov", value={"phone": "+998901234567", "code": "1234"}, request_only=True),
            OpenApiExample(
                "Javob",
                value={"access": "eyJ...", "refresh": "eyJ...", "is_new_user": True},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = PhoneVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        ok, message = verify_otp(phone, code)
        if not ok:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={"is_active": True},
        )

        AuthProvider.objects.get_or_create(
            user=user,
            provider_type=AuthProvider.ProviderType.PHONE,
            defaults={"provider_uid": phone},
        )

        tokens = issue_tokens_for_user(user)
        return Response({**tokens, "is_new_user": created})
