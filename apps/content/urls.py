from django.urls import path
from . import views

app_name = "content"

urlpatterns = [
    path("dashboard/inquiries/", views.dashboard_inquiries, name="dashboard_inquiries"),
    path("dashboard/inquiries/<int:pk>/resolve/", views.resolve_inquiry, name="resolve_inquiry"),
    path("dashboard/settings/", views.dashboard_settings, name="dashboard_settings"),
]
