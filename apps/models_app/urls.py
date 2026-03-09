from django.urls import path
from . import views

urlpatterns = [
    path("", views.model_list, name="model-list"),
    path("<slug:slug>/", views.model_detail, name="model-detail"),
]
