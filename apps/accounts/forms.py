from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = ("email", "full_name", "password1", "password2")
