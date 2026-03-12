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
    path("agency/<slug:agency_slug>/portfolio/add/", views.add_portfolio_item, name="agency-portfolio-add"),
    path("agency/portfolio/<int:item_id>/delete/", views.delete_portfolio_item, name="agency-portfolio-delete"),
]
