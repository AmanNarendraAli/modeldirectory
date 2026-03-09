from django.urls import path
from . import views

urlpatterns = [
    path("", views.agency_list, name="agency-list"),
    path("<slug:slug>/", views.agency_detail, name="agency-detail"),
]
