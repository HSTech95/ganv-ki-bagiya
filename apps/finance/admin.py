from django.contrib import admin
from .models import FundAccount, LedgerEntry, DailyBalanceSnapshot, AccountTransfer, BankReconciliation


@admin.register(FundAccount)
class FundAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "account_type", "current_balance", "bank_name", "account_number", "is_active")
    list_filter = ("account_type", "is_active")
    search_fields = ("name", "bank_name", "account_number")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_id", "entry_date", "entry_type", "account", "amount", "balance_after", "posted_by", "is_reversed")
    list_filter = ("entry_type", "account", "is_reversed", "entry_date")
    search_fields = ("entry_id", "description")
    readonly_fields = ("entry_id", "created_at")


@admin.register(DailyBalanceSnapshot)
class DailyBalanceSnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "opening_balance", "total_income", "total_expense", "closing_balance", "is_reconciled")
    list_filter = ("is_reconciled",)
    search_fields = ("date",)


@admin.register(AccountTransfer)
class AccountTransferAdmin(admin.ModelAdmin):
    list_display = ("transfer_id", "transfer_date", "from_account", "to_account", "amount", "initiated_by")
    list_filter = ("transfer_date",)
    search_fields = ("transfer_id", "reason")


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = ("account", "statement_date", "statement_balance", "book_balance", "discrepancy", "is_balanced")
    list_filter = ("is_balanced", "account")
    search_fields = ("account__name", "notes")
