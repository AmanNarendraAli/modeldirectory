from django.urls import path
from .views import SignupView, onboarding, delete_account, verify_email, resend_verification

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("onboarding/", onboarding, name="onboarding"),
    path("delete-account/", delete_account, name="delete-account"),
    path("verify-email/<uidb64>/<token>/", verify_email, name="verify-email"),
    path("resend-verification/", resend_verification, name="resend-verification"),
]
