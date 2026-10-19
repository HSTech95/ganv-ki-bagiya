from django.contrib import admin
from .models import Expense, ExpenseAttachment, ExpenseApprovalLog


class ExpenseAttachmentInline(admin.TabularInline):
    model = ExpenseAttachment
    extra = 1


class ExpenseApprovalLogInline(admin.TabularInline):
    model = ExpenseApprovalLog
    extra = 0
    readonly_fields = ("action", "user", "comments", "timestamp")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "expense_id", "expense_date", "category", "amount", "vendor_name",
        "approval_status", "payment_status", "is_posted_to_ledger"
    )
    list_filter = ("approval_status", "payment_status", "category", "expense_date")
    search_fields = ("expense_id", "description", "vendor_name", "bill_number")
    readonly_fields = ("expense_id", "created_at", "updated_at")
    inlines = [ExpenseAttachmentInline, ExpenseApprovalLogInline]


@admin.register(ExpenseAttachment)
class ExpenseAttachmentAdmin(admin.ModelAdmin):
    list_display = ("expense", "title", "file", "uploaded_at")


@admin.register(ExpenseApprovalLog)
class ExpenseApprovalLogAdmin(admin.ModelAdmin):
    list_display = ("expense", "action", "user", "timestamp")
    list_filter = ("action",)
    readonly_fields = ("expense", "action", "user", "comments", "timestamp")
