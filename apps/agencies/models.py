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
            candidate = slugify(self.name)
            if Agency.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                counter = 2
                while Agency.objects.filter(slug=f"{candidate}-{counter}").exclude(pk=self.pk).exists():
                    counter += 1
                candidate = f"{candidate}-{counter}"
            self.slug = candidate
        super().save(*args, **kwargs)


class AgencyRequirement(models.Model):
    class Category(models.TextChoices):
        ALL = "all", "All"
        EDITORIAL_MALE = "editorial_male", "Editorial (Male)"
        EDITORIAL_FEMALE = "editorial_female", "Editorial (Female)"
        RUNWAY_MALE = "runway_male", "Runway (Male)"
        RUNWAY_FEMALE = "runway_female", "Runway (Female)"
        COMMERCIAL_MALE = "commercial_male", "Commercial (Male)"
        COMMERCIAL_FEMALE = "commercial_female", "Commercial (Female)"

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="requirements")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ALL)
    min_height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    max_height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    min_bust_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    max_bust_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    min_waist_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    max_waist_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    min_hips_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    max_hips_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    min_inseam_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    max_inseam_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    preferred_hair_colors = models.CharField(
        max_length=200, blank=True,
        help_text="Comma-separated preferred hair colours, e.g. Brown, Black, Dark"
    )
    preferred_eye_colors = models.CharField(
        max_length=200, blank=True,
        help_text="Comma-separated preferred eye colours, e.g. Brown, Green, Hazel"
    )
    notes = models.TextField(blank=True)
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


class AgencyPortfolioPost(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="portfolio_posts")
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    caption = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="agencies/portfolio/covers/", blank=True, null=True)
    cover_image_thumbnail = ImageSpecField(source="cover_image", processors=[ResizeToFill(400, 400)], format="WEBP", options={"quality": 80})
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("agency", "slug")]

    def __str__(self):
        return f"{self.agency.name} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            candidate = slugify(self.title) or "untitled"
            if AgencyPortfolioPost.objects.filter(agency=self.agency, slug=candidate).exclude(pk=self.pk).exists():
                counter = 2
                while AgencyPortfolioPost.objects.filter(agency=self.agency, slug=f"{candidate}-{counter}").exclude(pk=self.pk).exists():
                    counter += 1
                candidate = f"{candidate}-{counter}"
            self.slug = candidate
        super().save(*args, **kwargs)


class AgencyPortfolioAsset(models.Model):
    portfolio_post = models.ForeignKey(AgencyPortfolioPost, on_delete=models.CASCADE, related_name="assets")
    image = models.ImageField(upload_to="agencies/portfolio/assets/")
    image_thumbnail = ImageSpecField(source="image", processors=[ResizeToFill(400, 400)], format="WEBP", options={"quality": 80})
    image_display = ImageSpecField(source="image", processors=[ResizeToFit(1200, 1200)], format="WEBP", options={"quality": 85})
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.portfolio_post.title} — asset {self.display_order}"


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


class AgencyRequest(models.Model):
    """Request to list a new agency on the platform."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    # Agency info
    agency_name = models.CharField(max_length=255)
    agency_city = models.CharField(max_length=100, blank=True)
    agency_website = models.URLField(blank=True)
    agency_instagram = models.URLField(blank=True)
    about_agency = models.TextField(blank=True, help_text="Tell us about your agency")

    # Person submitting
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    role_at_agency = models.CharField(max_length=100, blank=True, help_text="e.g. Owner, Booker, Manager")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_agency = models.OneToOneField(
        "Agency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_request",
        help_text="Auto-created when status is set to Accepted",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agency_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agency_name} — {self.contact_email}"
