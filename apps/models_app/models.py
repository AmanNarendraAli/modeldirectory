from django.conf import settings
from django.db import models
from django.utils.text import slugify


class ModelProfile(models.Model):
    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"

    class Gender(models.TextChoices):
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        NON_BINARY = "non_binary", "Non-binary"
        PREFER_NOT = "prefer_not_to_say", "Prefer not to say"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="model_profile"
    )
    public_display_name = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    profile_image = models.ImageField(upload_to="profiles/images/", blank=True, null=True)
    cover_image = models.ImageField(upload_to="profiles/covers/", blank=True, null=True)
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)

    # Measurements (in cm / numeric)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    bust_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    waist_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    hips_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    shoe_size = models.CharField(max_length=10, blank=True)
    hair_color = models.CharField(max_length=50, blank=True)
    eye_color = models.CharField(max_length=50, blank=True)

    # Links
    instagram_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)

    # Availability
    available_for_editorial = models.BooleanField(default=False)
    available_for_runway = models.BooleanField(default=False)
    available_for_commercial = models.BooleanField(default=False)
    available_for_fittings = models.BooleanField(default=False)

    # Agency representation (FK added later; leave nullable for independence)
    represented_by_agency = models.ForeignKey(
        "agencies.Agency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="represented_models",
    )

    is_public = models.BooleanField(default=False)
    is_discoverable = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Model Profile"

    def __str__(self):
        return self.public_display_name or self.user.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.public_display_name or self.user.full_name
            self.slug = slugify(base)
        if not self.public_display_name:
            self.public_display_name = self.user.full_name
        super().save(*args, **kwargs)
