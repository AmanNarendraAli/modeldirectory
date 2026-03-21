from django.db import models
from django.conf import settings
from django.utils.text import slugify


class ResourceArticle(models.Model):
    class Category(models.TextChoices):
        GUIDE = "guide", "Guide"
        NEWS = "news", "News"
        TRANSPARENCY = "transparency", "Transparency"
        TIPS = "tips", "Tips"

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    summary = models.CharField(max_length=500, blank=True)
    content = models.TextField()
    hero_image = models.ImageField(upload_to="resources/", blank=True, null=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GUIDE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Resource Article"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
