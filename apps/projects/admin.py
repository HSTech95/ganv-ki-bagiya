from django.contrib import admin
from .models import Project, ProjectUpdate


class ProjectUpdateInline(admin.TabularInline):
    model = ProjectUpdate
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "project_type", "estimated_budget", "start_date", "status", "progress_percentage", "is_public")
    list_filter = ("project_type", "status", "is_public")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProjectUpdateInline]


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ("project", "title", "update_date", "posted_by")
    list_filter = ("update_date",)
    search_fields = ("title", "content", "project__name")
