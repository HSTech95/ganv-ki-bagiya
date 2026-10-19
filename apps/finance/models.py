import uuid
from decimal import Decimal
# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser


class AccountType(models.TextChoices):
    CASH = "CASH", _("नकद पेटी (Cash in Hand)")
    BANK = "BANK", _("बैंक खाता (Bank Account)")
    ONLINE = "ONLINE", _("ऑनलाइन गेटवे (Online Gateway)")
    UPI = "UPI", _("यूपीआई खाता (UPI Account)")


class FundAccount(models.Model):
    name = models.CharField(max_length=150, verbose_name=_("खाते का नाम (Account Name)"))
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.BANK,
        verbose_name=_("खाते का प्रकार (Type)")
    )
    account_number = models.CharField(max_length=50, blank=True, verbose_name=_("खाता नंबर (Account Number)"))
    ifsc_code = models.CharField(max_length=20, blank=True, verbose_name=_("IFSC कोड (IFSC Code)"))
    bank_name = models.CharField(max_length=100, blank=True, verbose_name=_("बैंक का नाम (Bank Name)"))
    branch_name = models.CharField(max_length=100, blank=True, verbose_name=_("शाखा / ब्रांच (Branch)"))
    current_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("मौजूदा बैलेंस (Current Balance ₹)")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("चालू खाता (Active)"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["account_type", "name"]
        verbose_name = _("फंड खाता (Fund Account)")
        verbose_name_plural = _("फंड खाते (Fund Accounts)")

    def __str__(self):
        return f"{self.name} - ₹{self.current_balance:,.2f}"


class LedgerEntryType(models.TextChoices):
    INCOME = "INCOME", _("दान / आमदनी (+) (Income)")
    EXPENSE = "EXPENSE", _("खर्चा / भुगतान (-) (Expense)")
    TRANSFER_IN = "TRANSFER_IN", _("खाते में आया (+) (Transfer In)")
    TRANSFER_OUT = "TRANSFER_OUT", _("खाते से गया (-) (Transfer Out)")
    ADJUSTMENT_CREDIT = "ADJUSTMENT_CREDIT", _("हिसाब सुधार जमा (+) (Credit)")
    ADJUSTMENT_DEBIT = "ADJUSTMENT_DEBIT", _("हिसाब सुधार नामे (-) (Debit)")
    REVERSAL = "REVERSAL", _("गलत एंट्री का सुधार (Reversal)")


class LedgerEntry(models.Model):
    entry_id = models.CharField(max_length=35, unique=True, editable=False)
    entry_date = models.DateField(verbose_name=_("Entry Date"))
    entry_type = models.CharField(
        max_length=25,
        choices=LedgerEntryType.choices,
        verbose_name=_("Transaction Type")
    )
    account = models.ForeignKey(
        FundAccount,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
        verbose_name=_("Fund Account")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Transaction Amount (₹)")
    )
    balance_after = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Account Balance After (₹)")
    )
    description = models.CharField(max_length=255, verbose_name=_("Description / Narration"))
    
    # Audit & Links
    reference_donation = models.ForeignKey(
        "donations.Donation",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
        verbose_name=_("Linked Donation")
    )
    reference_expense = models.ForeignKey(
        "expenses.Expense",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
        verbose_name=_("Linked Expense")
    )
    reversal_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reversals",
        verbose_name=_("Original Reversal Target")
    )
    is_reversed = models.BooleanField(
        default=False,
        verbose_name=_("Has Been Reversed")
    )
    posted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name="posted_ledger_entries",
        verbose_name=_("Recorded By")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entry_date", "-created_at"]
        verbose_name = _("Ledger Entry")
        verbose_name_plural = _("Ledger Entries")

    def save(self, *args, **kwargs):
        if not self.entry_id:
            year_month = self.entry_date.strftime("%Y%m")
            short_uuid = uuid.uuid4().hex[:6].upper()
            self.entry_id = f"GKB-LEDG-{year_month}-{short_uuid}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.entry_id}] {self.entry_date} | {self.get_entry_type_display()} | ₹{self.amount}"


class DailyBalanceSnapshot(models.Model):
    date = models.DateField(unique=True, verbose_name=_("Date"))
    opening_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Opening Balance (₹)")
    )
    total_income = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Day's Confirmed Income (₹)")
    )
    total_expense = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Day's Paid Expense (₹)")
    )
    closing_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Closing Balance (₹)")
    )
    is_reconciled = models.BooleanField(
        default=False,
        verbose_name=_("Reconciled by Treasurer")
    )
    reconciled_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Reconciled By")
    )
    notes = models.TextField(blank=True, verbose_name=_("Audit Notes"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = _("Daily Balance Snapshot")
        verbose_name_plural = _("Daily Balance Snapshots")

    def __str__(self):
        return f"{self.date}: Open=₹{self.opening_balance:,.2f} | Income=₹{self.total_income:,.2f} | Exp=₹{self.total_expense:,.2f} | Close=₹{self.closing_balance:,.2f}"


class AccountTransfer(models.Model):
    transfer_id = models.CharField(max_length=35, unique=True, editable=False)
    transfer_date = models.DateField(verbose_name=_("Transfer Date"))
    from_account = models.ForeignKey(
        FundAccount,
        on_delete=models.PROTECT,
        related_name="transfers_out",
        verbose_name=_("Source Account")
    )
    to_account = models.ForeignKey(
        FundAccount,
        on_delete=models.PROTECT,
        related_name="transfers_in",
        verbose_name=_("Destination Account")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Transfer Amount (₹)")
    )
    reason = models.CharField(max_length=255, verbose_name=_("Purpose / Reason"))
    initiated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        verbose_name=_("Initiated By")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transfer_date", "-created_at"]
        verbose_name = _("Account Transfer")
        verbose_name_plural = _("Account Transfers")

    def save(self, *args, **kwargs):
        if not self.transfer_id:
            short_uuid = uuid.uuid4().hex[:6].upper()
            self.transfer_id = f"TRF-{self.transfer_date.strftime('%Y%m')}-{short_uuid}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.transfer_id}] {self.from_account.name} -> {self.to_account.name} (₹{self.amount})"


class BankReconciliation(models.Model):
    account = models.ForeignKey(
        FundAccount,
        on_delete=models.PROTECT,
        verbose_name=_("Account")
    )
    statement_date = models.DateField(verbose_name=_("Statement Date"))
    statement_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Bank Statement Balance (₹)")
    )
    book_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("System Book Balance (₹)")
    )
    discrepancy = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Discrepancy (₹)")
    )
    notes = models.TextField(blank=True, verbose_name=_("Reconciliation Notes"))
    verified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        verbose_name=_("Verified By")
    )
    is_balanced = models.BooleanField(default=True, verbose_name=_("Balanced & Verified"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-statement_date"]
        verbose_name = _("Bank Reconciliation")
        verbose_name_plural = _("Bank Reconciliations")

    def __str__(self):
        return f"{self.account.name} ({self.statement_date}) - Diff: ₹{self.discrepancy}"
