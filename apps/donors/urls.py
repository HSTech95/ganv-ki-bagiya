from django.urls import path
from . import views

app_name = "donors"

urlpatterns = [
    path("dashboard/donors/", views.dashboard_donor_list, name="dashboard_list"),
    path("dashboard/donors/create/", views.dashboard_donor_create, name="dashboard_create"),
    path("dashboard/donors/<int:pk>/", views.dashboard_donor_detail, name="dashboard_detail"),
    path("dashboard/donors/<int:pk>/edit/", views.dashboard_donor_edit, name="dashboard_edit"),
]
