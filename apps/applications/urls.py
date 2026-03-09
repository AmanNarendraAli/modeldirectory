from django.urls import path
from . import views

urlpatterns = [
    path("<slug:agency_slug>/apply/", views.apply, name="apply"),
    path("<slug:agency_slug>/apply/success/", views.apply_success, name="apply-success"),
]
