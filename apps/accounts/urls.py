from django.urls import path
from .views import SignupView, onboarding, delete_account

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("onboarding/", onboarding, name="onboarding"),
    path("delete-account/", delete_account, name="delete-account"),
]
