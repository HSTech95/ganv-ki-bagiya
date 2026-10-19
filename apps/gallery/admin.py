from django.contrib import admin
from .models import GalleryAlbum, GalleryItem


class GalleryItemInline(admin.TabularInline):
    model = GalleryItem
    extra = 1


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "event_date", "is_published", "created_at")
    list_filter = ("category", "is_published")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [GalleryItemInline]


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ("album", "title", "media_type", "is_before_after", "order", "uploaded_at")
    list_filter = ("media_type", "is_before_after")
    search_fields = ("title", "caption", "album__title")
