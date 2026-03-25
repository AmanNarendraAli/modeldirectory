import datetime

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit


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
    profile_image_thumbnail = ImageSpecField(source="profile_image", processors=[ResizeToFill(150, 150)], format="WEBP", options={"quality": 80})
    cover_image = models.ImageField(upload_to="profiles/covers/", blank=True, null=True)
    cover_image_optimized = ImageSpecField(source="cover_image", processors=[ResizeToFit(1200, 600)], format="WEBP", options={"quality": 85})
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)

    # Measurements (stored in cm, decimals allowed)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bust_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)  # labelled "Chest" for male models
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hips_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    inseam_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)  # primarily for male models
    shoe_size = models.CharField("Shoe Size (UK)", max_length=10, blank=True)
    hair_color = models.CharField(max_length=50, blank=True)
    eye_color = models.CharField(max_length=50, blank=True)

    # Links
    instagram_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

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
    custom_agency_name = models.CharField(
        max_length=255, blank=True,
        help_text="Agency name when the agency is not on the platform.",
    )

    is_public = models.BooleanField(default=False, db_index=True)
    is_discoverable = models.BooleanField(default=False, db_index=True)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Model Profile"

    def get_completeness(self):
        """Returns (percentage, missing_fields_list) tuple based on 12 checks."""
        checks = {
            "Profile image": bool(self.profile_image),
            "Bio": bool(self.bio),
            "City": bool(self.city),
            "Date of birth": bool(self.date_of_birth),
            "Gender": bool(self.gender),
            "Height": bool(self.height_cm),
            "Bust / Chest measurement": bool(self.bust_cm),
            "Waist measurement": bool(self.waist_cm),
            "Contact info (email or phone)": bool(self.contact_email or self.phone_number),
            "Social link (Instagram or website)": bool(self.instagram_url or self.website_url),
            "At least one portfolio post": self.portfolio_posts.filter(is_public=True).exists(),
            "Availability (at least one type)": any([self.available_for_editorial, self.available_for_runway, self.available_for_commercial, self.available_for_fittings]),
        }
        completed = sum(1 for v in checks.values() if v)
        total = len(checks)
        percentage = int(completed / total * 100)
        missing = [k for k, v in checks.items() if not v]
        return percentage, missing

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = datetime.date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def get_bust_chest_label(self):
        """Returns the correct label for bust_cm based on gender."""
        if self.gender == self.Gender.MALE:
            return "Chest"
        return "Bust"

    def __str__(self):
        return self.public_display_name or self.user.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.public_display_name or self.user.full_name
            candidate = slugify(base)
            # Ensure uniqueness — append a suffix if the slug is already taken
            if ModelProfile.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                counter = 2
                while ModelProfile.objects.filter(slug=f"{candidate}-{counter}").exclude(pk=self.pk).exists():
                    counter += 1
                candidate = f"{candidate}-{counter}"
            self.slug = candidate
        if not self.public_display_name:
            self.public_display_name = self.user.full_name
        super().save(*args, **kwargs)
