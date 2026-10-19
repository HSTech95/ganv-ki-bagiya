from django.urls import path
from . import views

app_name = "expenses"

urlpatterns = [
    path("dashboard/expenses/", views.dashboard_expenses_list, name="dashboard_list"),
    path("dashboard/expenses/create/", views.dashboard_expense_create, name="dashboard_create"),
    path("dashboard/expenses/<str:expense_id>/", views.dashboard_expense_detail, name="dashboard_detail"),
    path("dashboard/expenses/<str:expense_id>/approve/", views.dashboard_expense_approve, name="dashboard_approve"),
    path("dashboard/expenses/<str:expense_id>/pay/", views.dashboard_expense_pay, name="dashboard_pay"),
]
