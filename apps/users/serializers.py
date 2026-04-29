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
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        validators=[validate_email_domain],
    )
    # country = serializers.CharField(
    #     required=False,
    #     allow_blank=True,
    #     max_length=2,
    #     validators=[validate_country],
    # )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "avatar", "country"]

    def validate_email(self, value):
        if value is None:
            return value
        qs = User.objects.exclude(pk=self.instance.pk).filter(email=value)
        if qs.exists():
            raise serializers.ValidationError("Bu email allaqachon band.")
        return value

    def validate_country(self, value: str) -> str:
        return value.upper() if value else value
