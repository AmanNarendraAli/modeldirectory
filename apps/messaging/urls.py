from django.urls import path

from . import views

urlpatterns = [
    path("", views.inbox, name="message-inbox"),
    path("search/", views.search_users_for_messaging, name="search-users-for-messaging"),
    path("new/<slug:slug>/", views.start_conversation, name="start-conversation"),
    path("new-by-user/<int:user_id>/", views.start_conversation_with_user, name="start-conversation-with-user"),
    path("<int:pk>/", views.conversation_detail, name="conversation-detail"),
    path("<int:pk>/send/", views.send_message, name="send-message"),
    path("<int:pk>/accept/", views.accept_request, name="accept-request"),
    path("<int:pk>/decline/", views.decline_request, name="decline-request"),
    path("<int:pk>/block/", views.block_user, name="block-user"),
]
