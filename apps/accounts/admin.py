from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AuditLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Custom Role & Details", {
            "fields": ("role", "phone_number", "village_address", "profile_photo")
        }),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "first_name", "last_name", "email", "phone_number")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "target_model", "target_id")
    list_filter = ("action", "target_model")
    search_fields = ("details", "target_id", "user__username")
    readonly_fields = ("user", "action", "target_model", "target_id", "details", "ip_address", "timestamp")
