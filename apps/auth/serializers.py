from rest_framework import serializers

from apps.users.validators import validate_phone


class PhoneRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, validators=[validate_phone])


class PhoneVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, validators=[validate_phone])
    code = serializers.CharField(min_length=4, max_length=4)

    def validate_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak.")
        return value


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="Yangi JWT access token")
    refresh = serializers.CharField(help_text="Yangi JWT refresh token")


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="JWT access token (30 daqiqa)")
    refresh = serializers.CharField(help_text="JWT refresh token (7 kun)")
    is_new_user = serializers.BooleanField(help_text="True — yangi ro'yxatdan o'tgan foydalanuvchi")
