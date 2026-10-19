from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    # Public Transparency
    path("transparency/", views.transparency_view, name="transparency"),

    # Dashboard Ledger & Accounts
    path("dashboard/finance/ledger/", views.dashboard_ledger_view, name="dashboard_ledger"),
    path("dashboard/finance/daily-balances/", views.dashboard_daily_balances_view, name="dashboard_daily_balances"),
    path("dashboard/finance/accounts/", views.dashboard_accounts_view, name="dashboard_accounts"),
    path("dashboard/finance/transfer/", views.dashboard_transfer_view, name="dashboard_transfer"),
    path("dashboard/finance/reconciliation/", views.dashboard_reconciliation_view, name="dashboard_reconciliation"),
    path("dashboard/finance/reverse/", views.dashboard_reverse_entry_view, name="dashboard_reverse_entry"),
]
