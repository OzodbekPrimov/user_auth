from django.urls import path

from .views import GoogleAuthAPIView, LogoutAPIView, RefreshAccessTokenView, RequestOTPView, VerifyOTPView

urlpatterns = [
    path("phone/request/", RequestOTPView.as_view(), name="phone-request-otp"),
    path("phone/verify/", VerifyOTPView.as_view(), name="phone-verify-otp"),
    path("google/", GoogleAuthAPIView.as_view(), name="google-auth"),
    path("token/refresh/", RefreshAccessTokenView.as_view(), name="token-refresh"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
]
