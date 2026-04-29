from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework import generics
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    EmailChangeConfirmSerializer,
    EmailChangeRequestSerializer,
    ProfileReadSerializer,
    ProfileUpdateSerializer,
)
from .services.email_change import (
    EmailChangeRateLimitError,
    EmailDeliveryError,
    confirm_email_change,
    request_email_change,
)


@extend_schema(tags=["Profile"])
class ProfileView(generics.RetrieveUpdateAPIView):
    http_method_names = ["get", "patch"]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProfileReadSerializer
        return ProfileUpdateSerializer

    @extend_schema(
        summary="Profilni ko'rish",
        description="Joriy foydalanuvchi profili: shaxsiy ma'lumotlar, kirish usuli, sanalar.",
        responses={200: ProfileReadSerializer},
        examples=[
            OpenApiExample(
                "Javob",
                value={
                    "id": "uuid",
                    "phone": "+998901234567",
                    "email": None,
                    "first_name": "Ali",
                    "last_name": "Valiyev",
                    "full_name": "Ali Valiyev",
                    "avatar": "/media/avatars/2026/04/photo.jpg",
                    "country": "UZBEKISTAN",
                    "auth_methods": ["phone"],
                    "created_at": "2026-04-01T10:00:00Z",
                    "last_login": "2026-04-29T08:30:00Z",
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Profilni tahrirlash",
        description=(
            "Faqat yuborilgan maydonlar yangilanadi (partial update). "
            "Emailni yangilash uchun alohida tasdiqlash endpointlari ishlatiladi. "
            "Avatar yuborish uchun multipart/form-data ishlatilsin."
        ),
        request=ProfileUpdateSerializer,
        responses={
            200: ProfileReadSerializer,
            400: OpenApiResponse(description="Validatsiya xatosi"),
        },
        examples=[
            OpenApiExample(
                "So'rov",
                value={"first_name": "Ali", "last_name": "Valiyev", "country": "UZ"},
                request_only=True,
            )
        ],
    )
    def patch(self, request, *args, **kwargs):
        serializer = ProfileUpdateSerializer(
            self.get_object(),
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(ProfileReadSerializer(instance, context={"request": request}).data)


@extend_schema(tags=["Profile"])
class EmailChangeRequestView(APIView):
    @extend_schema(
        summary="Email o'zgartirish kodini yuborish",
        description="Yangi emailga 6 xonali tasdiqlash kodi yuboradi. Email profilga hali yozilmaydi.",
        request=EmailChangeRequestSerializer,
        responses={
            200: OpenApiResponse(description="Kod yuborildi"),
            400: OpenApiResponse(description="Validatsiya xatosi"),
            429: OpenApiResponse(description="Juda ko'p so'rov"),
            503: OpenApiResponse(description="Email yuborib bo'lmadi"),
        },
        examples=[
            OpenApiExample(
                "So'rov",
                value={"email": "new@example.com"},
                request_only=True,
            ),
            OpenApiExample(
                "Javob",
                value={"detail": "Tasdiqlash kodi emailga yuborildi."},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = EmailChangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            request_email_change(request.user, serializer.validated_data["email"])
        except EmailChangeRateLimitError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except EmailDeliveryError:
            return Response(
                {"detail": "Email yuborib bo'lmadi. Keyinroq urinib ko'ring."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"detail": "Tasdiqlash kodi emailga yuborildi."})


@extend_schema(tags=["Profile"])
class EmailChangeConfirmView(APIView):
    @extend_schema(
        summary="Email o'zgartirish kodini tasdiqlash",
        description="Kod to'g'ri bo'lsa, user emaili transaction ichida yangilanadi.",
        request=EmailChangeConfirmSerializer,
        responses={
            200: ProfileReadSerializer,
            400: OpenApiResponse(description="Kod noto'g'ri yoki validatsiya xatosi"),
        },
        examples=[
            OpenApiExample(
                "So'rov",
                value={"email": "new@example.com", "code": "123456"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = EmailChangeConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        confirm_email_change(
            request.user,
            serializer.validated_data["email"],
            serializer.validated_data["code"],
        )
        request.user.refresh_from_db()

        return Response(ProfileReadSerializer(request.user, context={"request": request}).data)
