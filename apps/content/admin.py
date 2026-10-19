from django.contrib import admin
from .models import Announcement, VolunteerRegistration, ContactSubmission, SiteSetting


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "badge_text", "is_active", "published_at", "expires_at")
    list_filter = ("is_active", "published_at")
    search_fields = ("title", "content")


@admin.register(VolunteerRegistration)
class VolunteerRegistrationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "village_mohalla", "skills_interest", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "phone", "skills_interest")


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "subject", "category", "is_resolved", "created_at")
    list_filter = ("category", "is_resolved", "created_at")
    search_fields = ("name", "phone", "subject", "message")


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("ngo_name", "contact_phone", "contact_email", "upi_id", "updated_at")
