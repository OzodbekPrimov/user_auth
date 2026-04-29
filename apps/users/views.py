from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .serializers import ProfileReadSerializer, ProfileUpdateSerializer


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
