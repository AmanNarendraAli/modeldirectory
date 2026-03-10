import logging

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_from_email():
    return getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@modellingdirectory.com")


def send_application_submitted_email(application):
    """Notify agency when a new application is submitted."""
    agency = application.agency
    applicant = application.applicant_profile

    from apps.agencies.models import AgencyStaff
    primary = AgencyStaff.objects.filter(agency=agency, is_primary_contact=True).select_related("user").first()
    recipient = primary.user.email if primary else agency.contact_email
    if not recipient:
        logger.warning("send_application_submitted_email: no recipient for agency %s", agency.id)
        return

    subject = f"New Application from {applicant.public_display_name} — The Modelling Directory"
    body = (
        f"You have received a new application.\n\n"
        f"Applicant: {applicant.public_display_name}\n"
        f"City: {applicant.city or '—'}\n"
        f"Height: {applicant.height_cm or '—'} cm\n\n"
        f"Log in to your dashboard to review the application."
    )

    logger.info("Sending application submitted email to %s (application %s)", recipient, application.id)
    try:
        send_mail(subject, body, _get_from_email(), [recipient], fail_silently=False)
        logger.info("Email sent successfully to %s", recipient)
    except Exception as exc:
        logger.error("Failed to send application submitted email to %s: %s", recipient, exc)


def send_status_changed_email(application):
    """Notify model when their application status is changed."""
    applicant = application.applicant_profile
    recipient = applicant.contact_email or applicant.user.email
    if not recipient:
        logger.warning("send_status_changed_email: no recipient for application %s", application.id)
        return

    subject = f"Application Update from {application.agency.name} — The Modelling Directory"
    body = (
        f"Your application to {application.agency.name} has been updated.\n\n"
        f"New status: {application.get_status_display()}\n"
    )
    if application.feedback:
        body += f"\nFeedback from {application.agency.name}:\n{application.feedback}\n"
    body += "\nLog in to your dashboard to view the full details."

    logger.info("Sending status changed email to %s (application %s)", recipient, application.id)
    try:
        send_mail(subject, body, _get_from_email(), [recipient], fail_silently=False)
        logger.info("Email sent successfully to %s", recipient)
    except Exception as exc:
        logger.error("Failed to send status changed email to %s: %s", recipient, exc)
