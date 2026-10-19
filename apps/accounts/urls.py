from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/profile/", views.profile_view, name="profile"),
    path("dashboard/users/", views.dashboard_users_list, name="dashboard_users"),
    path("dashboard/audit-logs/", views.dashboard_audit_logs_view, name="dashboard_audit_logs"),
]
