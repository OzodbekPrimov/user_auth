from django.urls import path

from .views import EmailChangeConfirmView, EmailChangeRequestView, ProfileView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="user-profile"),
    path("profile/email/request/", EmailChangeRequestView.as_view(), name="profile-email-request"),
    path("profile/email/verify/", EmailChangeConfirmView.as_view(), name="profile-email-verify"),
]
