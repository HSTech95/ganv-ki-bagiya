from django.contrib import admin
from .models import MaintenanceTask


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "facility", "task_type", "frequency", "scheduled_date", "priority", "status", "assigned_volunteer")
    list_filter = ("facility", "task_type", "status", "priority", "frequency")
    search_fields = ("title", "description", "completion_notes")
