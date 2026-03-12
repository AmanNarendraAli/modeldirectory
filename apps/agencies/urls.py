from django.urls import path
from . import views

urlpatterns = [
    path("", views.agency_list, name="agency-list"),
    path("<slug:slug>/", views.agency_detail, name="agency-detail"),
    path("<slug:slug>/portfolio/<int:post_id>/", views.agency_portfolio_detail, name="agency-portfolio-detail"),
]
