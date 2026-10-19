from django.contrib import admin
from .models import Donor


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "address", "is_anonymous", "created_at")
    list_filter = ("is_anonymous", "created_at")
    search_fields = ("name", "phone", "email", "address")
