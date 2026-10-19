from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    # Server-to-server Webhook
    path("payments/webhook/razorpay/", views.razorpay_webhook, name="razorpay_webhook"),

    # UPI Reconciliation in Staff Dashboard
    path("dashboard/finance/upi-reconciliation/", views.dashboard_upi_reconciliation_list, name="dashboard_upi_reconciliation"),
    path("dashboard/finance/upi-reconciliation/auto-match/", views.dashboard_upi_auto_match, name="dashboard_upi_auto_match"),
    path("dashboard/finance/upi-reconciliation/<int:record_id>/manual-match/", views.dashboard_upi_manual_match, name="dashboard_upi_manual_match"),
    path("dashboard/finance/upi-reconciliation/<int:record_id>/delete/", views.dashboard_upi_delete_record, name="dashboard_upi_delete_record"),
]
