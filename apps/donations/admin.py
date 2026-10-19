# pyrefly: ignore [missing-import]
from django.contrib import admin
from .models import Donation, DonationReceipt


class DonationReceiptInline(admin.StackedInline):
    model = DonationReceipt
    extra = 0
    readonly_fields = ("receipt_number", "issued_at")


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        "donation_id", "donor_name", "amount", "purpose", "payment_method",
        "payment_status", "is_posted_to_ledger", "donation_date"
    )
    list_filter = ("payment_status", "payment_method", "purpose", "is_posted_to_ledger", "donation_date")
    search_fields = ("donation_id", "receipt_number", "donor_name", "donor_phone", "transaction_reference")
    readonly_fields = ("donation_id", "receipt_number", "created_at", "updated_at")
    inlines = [DonationReceiptInline]


@admin.register(DonationReceipt)
class DonationReceiptAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "donation", "issued_at", "issued_by")
    search_fields = ("receipt_number", "donation__donor_name")
