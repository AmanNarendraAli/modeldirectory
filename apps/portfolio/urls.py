from django.urls import path
from . import views

urlpatterns = [
    path("new/", views.portfolio_create, name="portfolio-create"),
    path("<slug:slug>/", views.portfolio_detail, name="portfolio-detail"),
    path("<slug:slug>/edit/", views.portfolio_edit, name="portfolio-edit"),
    path("<slug:slug>/delete/", views.portfolio_delete, name="portfolio-delete"),
]
