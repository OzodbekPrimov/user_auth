from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import EmailChangeRequest, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("get_display_name", "phone", "email", "country", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff", "country")
    search_fields = ("phone", "email", "first_name", "last_name")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at", "last_login")

    fieldsets = (
        (None, {"fields": ("id", "phone", "email", "password")}),
        ("Shaxsiy ma'lumot", {"fields": ("first_name", "last_name", "avatar", "country")}),
        ("Huquqlar", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Vaqtlar", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "email", "password1", "password2"),
        }),
    )


@admin.register(EmailChangeRequest)
class EmailChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "is_used", "attempts", "expires_at", "created_at")
    list_filter = ("is_used", "created_at", "expires_at")
    search_fields = ("user__phone", "user__email", "email")
    readonly_fields = ("id", "user", "email", "code_hash", "attempts", "is_used", "created_at", "used_at")
    ordering = ("-created_at",)
