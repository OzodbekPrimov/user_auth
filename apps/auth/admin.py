from django.contrib import admin

from .models import AuthProvider, OTPCode


@admin.register(AuthProvider)
class AuthProviderAdmin(admin.ModelAdmin):
    list_display = ("user", "provider_type", "provider_uid", "created_at")
    list_filter = ("provider_type",)
    search_fields = ("user__phone", "user__email", "provider_uid")
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "is_used", "attempts", "expires_at", "created_at")
    list_filter = ("is_used",)
    search_fields = ("phone",)
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False
