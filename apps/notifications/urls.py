from django.urls import path

from . import views

urlpatterns = [
    path("", views.notification_list, name="notification-list"),
    path("mark-read/", views.mark_notifications_read, name="mark-notifications-read"),
]
