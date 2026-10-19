from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("dashboard/reports/", views.reports_index, name="index"),
    path("dashboard/reports/donations/csv/", views.export_donations_csv, name="donations_csv"),
    path("dashboard/reports/donations/excel/", views.export_donations_excel, name="donations_excel"),
    path("dashboard/reports/expenses/csv/", views.export_expenses_csv, name="expenses_csv"),
    path("dashboard/reports/expenses/excel/", views.export_expenses_excel, name="expenses_excel"),
    path("dashboard/reports/ledger/excel/", views.export_ledger_excel, name="ledger_excel"),
    path("dashboard/reports/financial-statement/pdf/", views.export_financial_statement_pdf, name="financial_statement_pdf"),
]
