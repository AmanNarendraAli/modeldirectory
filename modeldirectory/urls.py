from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts.views import VerifiedPasswordResetView

handler400 = "apps.core.views.error_400"
handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"

urlpatterns = [
    path("admin/", admin.site.urls),

    # Custom password reset (must be before django.contrib.auth.urls to override)
    path("accounts/password_reset/", VerifiedPasswordResetView.as_view(), name="password_reset"),

    # Auth (Django built-in: login, logout, password reset confirm/done/complete, etc.)
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("apps.accounts.urls")),

    # Core (landing page)
    path("", include("apps.core.urls")),

    # Agencies
    path("agencies/", include("apps.agencies.urls")),

    # Models
    path("models/", include("apps.models_app.urls")),

    # Portfolio
    path("portfolio/", include("apps.portfolio.urls")),

    # Applications
    path("agencies/", include("apps.applications.urls")),

    # Discovery toggles (save/follow)
    path("", include("apps.discovery.urls")),

    # Dashboard (model + agency, role-routed)
    path("dashboard/", include("apps.dashboard.urls")),

    # Resources / transparency
    path("resources/", include("apps.resources.urls")),

    # Notifications
    path("notifications/", include("apps.notifications.urls")),

    # Messaging
    path("messages/", include("apps.messaging.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
