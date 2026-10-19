from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    # Public
    path("projects/", views.projects_list, name="public_list"),
    path("projects/<slug:slug>/", views.project_detail, name="public_detail"),

    # Dashboard
    path("dashboard/projects/", views.dashboard_projects_list, name="dashboard_list"),
    path("dashboard/projects/create/", views.dashboard_project_create, name="dashboard_create"),
    path("dashboard/projects/<int:pk>/", views.dashboard_project_detail, name="dashboard_detail"),
    path("dashboard/projects/<int:pk>/edit/", views.dashboard_project_edit, name="dashboard_edit"),
]
