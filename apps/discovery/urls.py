from django.urls import path
from . import views

urlpatterns = [
    path("agencies/<slug:slug>/save/", views.save_agency, name="save-agency"),
    path("models/<slug:slug>/follow/", views.follow_model, name="follow-model"),
]
