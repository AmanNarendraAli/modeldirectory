from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/edit/", views.edit_profile, name="edit-profile"),
    path("applications/<int:application_id>/", views.applicant_detail, name="applicant-detail"),
    path("applications/<int:application_id>/status/", views.update_application_status, name="update-application-status"),
]
