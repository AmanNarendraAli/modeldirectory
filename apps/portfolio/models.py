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
        unique_together = [("owner_profile", "slug")]

    def __str__(self):
        return f"{self.owner_profile} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            candidate = slugify(self.title) or "untitled"
            if PortfolioPost.objects.filter(owner_profile=self.owner_profile, slug=candidate).exclude(pk=self.pk).exists():
                counter = 2
                while PortfolioPost.objects.filter(owner_profile=self.owner_profile, slug=f"{candidate}-{counter}").exclude(pk=self.pk).exists():
                    counter += 1
                candidate = f"{candidate}-{counter}"
            self.slug = candidate
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
