from django.contrib import admin
from .models import PaymentTransaction, UPIReconciliationRecord


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("gateway_payment_id", "gateway_order_id", "donation", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("gateway_payment_id", "gateway_order_id", "donation__donation_id")


@admin.register(UPIReconciliationRecord)
class UPIReconciliationRecordAdmin(admin.ModelAdmin):
    list_display = ("utr_number", "bank_statement_date", "amount", "payer_details", "is_matched", "matched_donation")
    list_filter = ("is_matched", "bank_statement_date")
    search_fields = ("utr_number", "payer_details")
