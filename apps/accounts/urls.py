from django.urls import path
from .views import SignupView, onboarding

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("onboarding/", onboarding, name="onboarding"),
]
