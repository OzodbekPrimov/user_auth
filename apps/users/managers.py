from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Phone yoki email bilan user yaratish."""

    def _create_user(self, phone=None, email=None, password=None, **extra_fields):
        if not phone and not email:
            raise ValueError("Phone yoki email berilishi kerak.")

        if email:
            email = self.normalize_email(email)

        user = self.model(phone=phone, email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            # Social/phone auth — password ishlatilmaydi
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(self, phone=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, email, password, **extra_fields)

    def create_superuser(self, phone=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone=phone, email=email, password=password, **extra_fields)