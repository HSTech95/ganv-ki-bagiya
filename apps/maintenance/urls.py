from django.urls import path
from . import views

app_name = "maintenance"

urlpatterns = [
    path("dashboard/maintenance/", views.dashboard_maintenance_list, name="dashboard_list"),
    path("dashboard/maintenance/create/", views.dashboard_maintenance_create, name="dashboard_create"),
    path("dashboard/maintenance/<int:pk>/", views.dashboard_maintenance_detail, name="dashboard_detail"),
]
