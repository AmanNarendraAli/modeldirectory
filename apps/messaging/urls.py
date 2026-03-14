from django.urls import path

from . import views

urlpatterns = [
    path("", views.inbox, name="message-inbox"),
    path("new/<slug:slug>/", views.start_conversation, name="start-conversation"),
    path("<int:pk>/", views.conversation_detail, name="conversation-detail"),
    path("<int:pk>/send/", views.send_message, name="send-message"),
    path("<int:pk>/accept/", views.accept_request, name="accept-request"),
    path("<int:pk>/decline/", views.decline_request, name="decline-request"),
    path("<int:pk>/block/", views.block_user, name="block-user"),
]
