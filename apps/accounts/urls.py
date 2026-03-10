from django.urls import path
from .views import SignupView, onboarding, switch_role, delete_account

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("onboarding/", onboarding, name="onboarding"),
    path("switch-role/", switch_role, name="switch-role"),
    path("delete-account/", delete_account, name="delete-account"),
]
