from django.conf import settings
from django.db import models


class Application(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        SHORTLISTED = "shortlisted", "Shortlisted"
        CONTACTED = "contacted", "Contacted"
        SIGNED = "signed", "Signed"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    applicant_profile = models.ForeignKey(
        "models_app.ModelProfile", on_delete=models.CASCADE, related_name="applications"
    )
    agency = models.ForeignKey("agencies.Agency", on_delete=models.CASCADE, related_name="applications")
    agency_requirement = models.ForeignKey(
        "agencies.AgencyRequirement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    cover_note = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    feedback_updated_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        unique_together = [("applicant_profile", "agency")]

    def __str__(self):
        return f"{self.applicant_profile} → {self.agency} [{self.status}]"


class ApplicationSnapshot(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="snapshot")
    applicant_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=20, blank=True)  # snapshot of gender at submission time
    city = models.CharField(max_length=100, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bust_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)  # also used as "chest" for male models
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hips_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    inseam_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    portfolio_summary = models.TextField(blank=True)
    selected_portfolio_posts = models.JSONField(default=list, blank=True)
    submission_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Snapshot for {self.application}"
