from django.conf import settings
from django.db import models
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit


class Agency(models.Model):
    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to="agencies/logos/", blank=True, null=True)
    logo_thumbnail = ImageSpecField(source="logo", processors=[ResizeToFill(200, 200)], format="WEBP", options={"quality": 80})
    cover_image = models.ImageField(upload_to="agencies/covers/", blank=True, null=True)
    cover_image_optimized = ImageSpecField(source="cover_image", processors=[ResizeToFit(1200, 600)], format="WEBP", options={"quality": 85})
    short_tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    headquarters_address = models.CharField(max_length=255, blank=True)
    website_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
    featured_order = models.PositiveSmallIntegerField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED
    )
    is_active = models.BooleanField(default=True)
    is_accepting_applications = models.BooleanField(default=False)
    is_roster_public = models.BooleanField(default=False)
    is_requirements_public = models.BooleanField(default=True)
    created_by_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_agencies",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["featured_order", "name"]
        verbose_name_plural = "Agencies"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class AgencyRequirement(models.Model):
    class Category(models.TextChoices):
        MENSWEAR = "menswear", "Menswear"
        WOMENSWEAR = "womenswear", "Womenswear"
        ALL = "all", "All"
        EDITORIAL = "editorial", "Editorial"
        COMMERCIAL = "commercial", "Commercial"
        RUNWAY = "runway", "Runway"

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="requirements")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ALL)
    min_height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    max_height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    accepts_beginners = models.BooleanField(default=False)
    application_guidance_text = models.TextField(blank=True)
    active_from = models.DateField(null=True, blank=True)
    active_to = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_current", "category"]

    def __str__(self):
        return f"{self.agency.name} — {self.get_category_display()} requirements"


class AgencyHighlight(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="highlights")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    related_model_name = models.CharField(max_length=255, blank=True)
    related_brand_name = models.CharField(max_length=255, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to="agencies/highlights/", blank=True, null=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.agency.name} — {self.title}"


class AgencyBan(models.Model):
    """Records when an agency removes a model — prevents the model from self-adding back."""
    model_profile = models.ForeignKey(
        "models_app.ModelProfile",
        on_delete=models.CASCADE,
        related_name="agency_bans",
    )
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="banned_models")
    banned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("model_profile", "agency")]

    def __str__(self):
        return f"{self.model_profile} banned from {self.agency}"


class AgencyStaff(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agency_staff_roles"
    )
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="staff")
    role_title = models.CharField(max_length=100, blank=True)
    can_review_applications = models.BooleanField(default=True)
    can_edit_agency = models.BooleanField(default=False)
    is_primary_contact = models.BooleanField(default=False)

    class Meta:
        unique_together = [("user", "agency")]
        verbose_name_plural = "Agency Staff"

    def __str__(self):
        return f"{self.user} @ {self.agency}"
