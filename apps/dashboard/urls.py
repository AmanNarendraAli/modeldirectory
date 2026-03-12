from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/edit/", views.edit_profile, name="edit-profile"),
    path("agency/edit/", views.edit_agency, name="edit-agency"),
    path("applications/<int:application_id>/", views.applicant_detail, name="applicant-detail"),
    path("applications/<int:application_id>/status/", views.update_application_status, name="update-application-status"),
    path("applications/<int:application_id>/feedback/", views.submit_feedback, name="submit-feedback"),
    path("agency/<int:agency_id>/link-model/", views.link_model, name="link-model"),
    path("agency/<int:agency_id>/unlink-model/<int:model_id>/", views.unlink_model, name="unlink-model"),
    path("agency/<int:agency_id>/search-models/", views.search_models_for_roster, name="search-models-for-roster"),
    path("agency/portfolio/new/", views.agency_portfolio_create, name="agency-portfolio-create"),
    path("agency/portfolio/<int:post_id>/edit/", views.agency_portfolio_edit, name="agency-portfolio-edit"),
    path("agency/portfolio/<int:post_id>/delete/", views.agency_portfolio_delete, name="agency-portfolio-delete"),
]
