# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.utils.text import slugify
# pyrefly: ignore [missing-import]
from django.utils.translation import gettext_lazy as _


class AlbumCategory(models.TextChoices):
    GARDEN_TRANSFORMATION = "GARDEN_TRANSFORMATION", _("बगिया की हरियाली (Garden Transformation)")
    KABRISTAN_CLEANING = "KABRISTAN_CLEANING", _("कब्रिस्तान की साफ़-सफ़ाई (Kabristan Cleaning)")
    TREE_PLANTATION = "TREE_PLANTATION", _("पेड़-पौधे लगाना (Tree Plantation)")
    COMMUNITY_MEETING = "COMMUNITY_MEETING", _("गाँव वालों की बैठक व श्रमदान (Community Meeting)")
    BEFORE_AFTER = "BEFORE_AFTER", _("पहले और अब (Before & After)")
    EVENTS = "EVENTS", _("गाँव के कार्यक्रम (Community Events)")


class GalleryAlbum(models.Model):
    title = models.CharField(max_length=150, verbose_name=_("Album Title"))
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    category = models.CharField(
        max_length=35,
        choices=AlbumCategory.choices,
        default=AlbumCategory.GARDEN_TRANSFORMATION,
        verbose_name=_("Category")
    )
    description = models.TextField(blank=True, verbose_name=_("Album Description"))
    cover_image = models.ImageField(
        upload_to="gallery/covers/",
        blank=True,
        null=True,
        verbose_name=_("Cover Image")
    )
    event_date = models.DateField(null=True, blank=True, verbose_name=_("Event / Activity Date"))
    is_published = models.BooleanField(default=True, verbose_name=_("Published"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-event_date", "-created_at"]
        verbose_name = _("Gallery Album")
        verbose_name_plural = _("Gallery Albums")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "album"
            slug = base_slug
            counter = 1
            while GalleryAlbum.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class GalleryItem(models.Model):
    album = models.ForeignKey(
        GalleryAlbum,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Album")
    )
    title = models.CharField(max_length=200, blank=True, verbose_name=_("Title / Caption"))
    media_type = models.CharField(
        max_length=15,
        choices=[("PHOTO", _("Photograph")), ("VIDEO_LINK", _("Video Link (YouTube)"))],
        default="PHOTO",
        verbose_name=_("Media Type")
    )
    image = models.ImageField(
        upload_to="gallery/photos/",
        blank=True,
        null=True,
        verbose_name=_("Photo")
    )
    video_url = models.URLField(blank=True, verbose_name=_("Video Embed / Watch Link"))
    caption = models.TextField(blank=True, verbose_name=_("Detailed Description / Context"))
    
    # Before & After Support
    is_before_after = models.BooleanField(
        default=False,
        verbose_name=_("Is Before-and-After Comparison")
    )
    before_image = models.ImageField(
        upload_to="gallery/before_after/",
        blank=True,
        null=True,
        verbose_name=_("Before Photo (पहले की स्थिति)")
    )
    after_image = models.ImageField(
        upload_to="gallery/before_after/",
        blank=True,
        null=True,
        verbose_name=_("After Photo (अब की स्थिति)")
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-uploaded_at"]
        verbose_name = _("Gallery Media Item")
        verbose_name_plural = _("Gallery Media Items")

    def __str__(self):
        return f"{self.album.title} - {self.title or 'Media Item #' + str(self.id)}"
