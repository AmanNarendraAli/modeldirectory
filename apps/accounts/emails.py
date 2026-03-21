import logging

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.core.emails import _get_from_email

logger = logging.getLogger(__name__)


def send_verification_email(user, request):
    """Send email verification link to the user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse("verify-email", args=[uid, token])
    )

    subject = "Welcome! Please verify your email — The Modelling Directory"
    html_body = render_to_string("accounts/emails/verify_email.html", {
        "user": user,
        "verify_url": verify_url,
    })
    plain_body = (
        f"Hi {user.full_name},\n\n"
        f"Welcome to The Modelling Directory! Please verify your email by visiting:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in 3 days.\n\n"
        f"— The Modelling Directory"
    )

    logger.info("Sending verification email to %s (user %s)", user.email, user.pk)
    try:
        send_mail(
            subject,
            plain_body,
            _get_from_email(),
            [user.email],
            html_message=html_body,
            fail_silently=False,
        )
        logger.info("Verification email sent to %s", user.email)
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", user.email, exc)
