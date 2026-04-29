from django.contrib.auth import get_user_model
from rest_framework import serializers

from .validators import validate_email_domain

User = get_user_model()


class ProfileReadSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    auth_methods = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "country",
            "auth_methods",
            "created_at",
            "last_login",
        ]

    def get_auth_methods(self, obj) -> list[str]:
        return list(obj.auth_providers.values_list("provider_type", flat=True))


class ProfileUpdateSerializer(serializers.ModelSerializer):
    # country = serializers.CharField(
    #     required=False,
    #     allow_blank=True,
    #     max_length=2,
    #     validators=[validate_country],
    # )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar", "country"]

    def validate(self, attrs):
        if "email" in self.initial_data:
            raise serializers.ValidationError(
                {"email": "Emailni yangilash uchun /profile/email/request/ endpointidan foydalaning."}
            )
        return attrs

    def validate_country(self, value: str) -> str:
        return value.upper() if value else value


class EmailChangeRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_email_domain])


class EmailChangeConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_email_domain])
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak.")
        return value
