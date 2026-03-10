from django.db import models
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit


class PortfolioPost(models.Model):
    owner_profile = models.ForeignKey(
        "models_app.ModelProfile", on_delete=models.CASCADE, related_name="portfolio_posts"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    caption = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="portfolio/covers/", blank=True, null=True)
    cover_image_thumbnail = ImageSpecField(source="cover_image", processors=[ResizeToFill(400, 400)], format="WEBP", options={"quality": 80})
    is_public = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.owner_profile} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class PortfolioAsset(models.Model):
    portfolio_post = models.ForeignKey(PortfolioPost, on_delete=models.CASCADE, related_name="assets")
    image = models.ImageField(upload_to="portfolio/assets/")
    image_thumbnail = ImageSpecField(source="image", processors=[ResizeToFill(400, 400)], format="WEBP", options={"quality": 80})
    image_display = ImageSpecField(source="image", processors=[ResizeToFit(1200, 1200)], format="WEBP", options={"quality": 85})
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.portfolio_post.title} — asset {self.display_order}"
