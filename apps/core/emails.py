from django.core.mail import send_mail
from django.conf import settings


def _get_from_email():
    return getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@modellingdirectory.com")


def send_application_submitted_email(application):
    """Notify agency when a new application is submitted."""
    agency = application.agency
    applicant = application.applicant_profile

    # Try primary contact staff first, then agency contact email
    from apps.agencies.models import AgencyStaff
    primary = AgencyStaff.objects.filter(agency=agency, is_primary_contact=True).select_related("user").first()
    recipient = primary.user.email if primary else agency.contact_email
    if not recipient:
        return

    subject = f"New Application from {applicant.public_display_name} — The Modelling Directory"
    body = (
        f"You have received a new application.\n\n"
        f"Applicant: {applicant.public_display_name}\n"
        f"City: {applicant.city or '—'}\n"
        f"Height: {applicant.height_cm or '—'} cm\n\n"
        f"Log in to your dashboard to review the application."
    )
    send_mail(subject, body, _get_from_email(), [recipient], fail_silently=True)


def send_status_changed_email(application):
    """Notify model when their application status is changed."""
    applicant = application.applicant_profile
    recipient = applicant.contact_email or applicant.user.email
    if not recipient:
        return

    subject = f"Application Update from {application.agency.name} — The Modelling Directory"
    body = (
        f"Your application to {application.agency.name} has been updated.\n\n"
        f"New status: {application.get_status_display()}\n"
    )
    if application.feedback:
        body += f"\nFeedback from {application.agency.name}:\n{application.feedback}\n"
    body += "\nLog in to your dashboard to view the full details."

    send_mail(subject, body, _get_from_email(), [recipient], fail_silently=True)
