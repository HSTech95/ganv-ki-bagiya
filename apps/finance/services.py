from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from .models import (
    FundAccount, LedgerEntry, LedgerEntryType,
    DailyBalanceSnapshot, AccountTransfer, BankReconciliation,
    AccountType
)
from apps.accounts.models import AuditLog
from apps.donations.models import Donation, PaymentStatus
from apps.expenses.models import Expense, ExpenseApprovalStatus, ExpensePaymentStatus


def get_financial_summary(start_date=None, end_date=None, project_id=None):
    """
    Returns verified, immutable ledger-based financial summary.
    Never hardcoded. Always computed from accounts & confirmed transactions.
    """
    # Current balances in active accounts
    accounts = FundAccount.objects.filter(is_active=True)
    cash_balance = accounts.filter(account_type=AccountType.CASH).aggregate(total=models.Sum("current_balance"))["total"] or Decimal("0.00")
    bank_balance = accounts.filter(account_type=AccountType.BANK).aggregate(total=models.Sum("current_balance"))["total"] or Decimal("0.00")
    online_balance = accounts.filter(account_type__in=[AccountType.ONLINE, AccountType.UPI]).aggregate(total=models.Sum("current_balance"))["total"] or Decimal("0.00")
    current_book_balance = accounts.aggregate(total=models.Sum("current_balance"))["total"] or Decimal("0.00")

    # Confirmed income query
    donations_qs = Donation.objects.filter(payment_status=PaymentStatus.CONFIRMED)
    if start_date:
        donations_qs = donations_qs.filter(donation_date__gte=start_date)
    if end_date:
        donations_qs = donations_qs.filter(donation_date__lte=end_date)
    if project_id:
        donations_qs = donations_qs.filter(related_project=project_id)
    total_confirmed_donations = donations_qs.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
    donor_count = donations_qs.values("donor").distinct().count()

    # Paid expenses query
    expenses_qs = Expense.objects.filter(payment_status=ExpensePaymentStatus.PAID)
    if start_date:
        expenses_qs = expenses_qs.filter(expense_date__gte=start_date)
    if end_date:
        expenses_qs = expenses_qs.filter(expense_date__lte=end_date)
    if project_id:
        expenses_qs = expenses_qs.filter(related_project=project_id)
    total_expenses_paid = expenses_qs.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    # Pending approvals & payments
    pending_approvals = Expense.objects.filter(approval_status=ExpenseApprovalStatus.SUBMITTED)
    pending_approvals_count = pending_approvals.count()
    pending_approvals_amount = pending_approvals.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    pending_payments = Expense.objects.filter(
        approval_status=ExpenseApprovalStatus.APPROVED,
        payment_status=ExpensePaymentStatus.UNPAID
    )
    pending_payments_count = pending_payments.count()
    pending_payments_amount = pending_payments.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    pending_donations = Donation.objects.filter(payment_status=PaymentStatus.PENDING)
    pending_donations_count = pending_donations.count()
    pending_donations_amount = pending_donations.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    # Last bank reconciliation
    last_recon = BankReconciliation.objects.order_by("-statement_date").first()

    # Financial Discrepancy Detection (Section 8 requirement)
    discrepancy_alert = None
    if accounts.filter(current_balance__lt=Decimal("0.00")).exists():
        discrepancy_alert = "सावधान: एक या अधिक कोष खातों में ऋणात्मक (Negative) शेष पाया गया है!"
    else:
        latest_snapshot = DailyBalanceSnapshot.objects.order_by("-date").first()
        if latest_snapshot:
            expected_closing = latest_snapshot.opening_balance + latest_snapshot.total_income - latest_snapshot.total_expense
            if abs(latest_snapshot.closing_balance - expected_closing) > Decimal("0.01"):
                discrepancy_alert = f"दैनिक बैलेंस अंतर: दिनांक {latest_snapshot.date} के दर्ज शेष (₹{latest_snapshot.closing_balance}) तथा परिकलित शेष (₹{expected_closing}) में विसंगति है।"

    return {
        "current_book_balance": current_book_balance,
        "cash_balance": cash_balance,
        "bank_balance": bank_balance,
        "online_balance": online_balance,
        "total_confirmed_donations": total_confirmed_donations,
        "total_expenses_paid": total_expenses_paid,
        "donor_count": donor_count,
        "pending_approvals_count": pending_approvals_count,
        "pending_approvals_amount": pending_approvals_amount,
        "pending_payments_count": pending_payments_count,
        "pending_payments_amount": pending_payments_amount,
        "pending_donations_count": pending_donations_count,
        "pending_donations_amount": pending_donations_amount,
        "last_reconciliation_date": last_recon.statement_date if last_recon else None,
        "discrepancy_alert": discrepancy_alert,
    }


def calculate_daily_balance(target_date):
    """
    Computes or updates the DailyBalanceSnapshot for a given target_date.
    Closing balance = Opening balance + Confirmed income - Paid expenses.
    Opening balance equals the previous day's closing balance (or 0 for earliest date).
    """
    previous_snapshot = DailyBalanceSnapshot.objects.filter(date__lt=target_date).order_by("-date").first()
    opening_balance = previous_snapshot.closing_balance if previous_snapshot else Decimal("0.00")

    # Income on target_date from posted ledger entries
    income_entries = LedgerEntry.objects.filter(
        entry_date=target_date,
        entry_type__in=[LedgerEntryType.INCOME, LedgerEntryType.ADJUSTMENT_CREDIT],
        is_reversed=False
    )
    day_income = income_entries.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    # Expenses on target_date from posted ledger entries
    expense_entries = LedgerEntry.objects.filter(
        entry_date=target_date,
        entry_type__in=[LedgerEntryType.EXPENSE, LedgerEntryType.ADJUSTMENT_DEBIT],
        is_reversed=False
    )
    day_expense = expense_entries.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    closing_balance = opening_balance + day_income - day_expense

    snapshot, created = DailyBalanceSnapshot.objects.update_or_create(
        date=target_date,
        defaults={
            "opening_balance": opening_balance,
            "total_income": day_income,
            "total_expense": day_expense,
            "closing_balance": closing_balance,
        }
    )
    return snapshot


def execute_account_transfer(from_account, to_account, amount, reason, user, transfer_date=None):
    """
    Transfers funds atomically between two fund accounts without inflating income/expenses.
    Creates TRANSFER_OUT and TRANSFER_IN entries in the ledger.
    """
    if from_account.pk == to_account.pk:
        return False, "Source and destination accounts must be different."
    if amount <= Decimal("0.00"):
        return False, "Transfer amount must be strictly greater than zero."

    exec_date = transfer_date or timezone.now().date()

    with transaction.atomic():
        src = FundAccount.objects.select_for_update().get(pk=from_account.pk)
        dst = FundAccount.objects.select_for_update().get(pk=to_account.pk)

        if src.current_balance < amount:
            return False, f"Insufficient balance in {src.name}. Available: ₹{src.current_balance}"

        src.current_balance -= amount
        dst.current_balance += amount
        src.save()
        dst.save()

        # Ledger OUT
        LedgerEntry.objects.create(
            entry_date=exec_date,
            entry_type=LedgerEntryType.TRANSFER_OUT,
            account=src,
            amount=amount,
            balance_after=src.current_balance,
            description=f"Internal transfer to {dst.name}: {reason}",
            posted_by=user
        )

        # Ledger IN
        LedgerEntry.objects.create(
            entry_date=exec_date,
            entry_type=LedgerEntryType.TRANSFER_IN,
            account=dst,
            amount=amount,
            balance_after=dst.current_balance,
            description=f"Internal transfer from {src.name}: {reason}",
            posted_by=user
        )

        transfer_record = AccountTransfer.objects.create(
            transfer_date=exec_date,
            from_account=src,
            to_account=dst,
            amount=amount,
            reason=reason,
            initiated_by=user
        )

        AuditLog.objects.create(
            user=user,
            action="ACCOUNT_TRANSFER",
            target_model="AccountTransfer",
            target_id=transfer_record.transfer_id,
            details=f"Transferred ₹{amount} from {src.name} to {dst.name} ({reason})"
        )

    return True, "Fund transfer completed successfully."


def reverse_ledger_entry(entry_id, user, reason):
    """
    Creates an immutable reversal entry to correct an erroneous posted transaction.
    Original entry is marked is_reversed=True.
    """
    try:
        orig = LedgerEntry.objects.get(entry_id=entry_id)
    except LedgerEntry.DoesNotExist:
        return False, "Ledger entry not found."

    if orig.is_reversed:
        return False, "Entry has already been reversed."

    with transaction.atomic():
        account = FundAccount.objects.select_for_update().get(pk=orig.account.pk)
        today = timezone.now().date()

        if orig.entry_type in [LedgerEntryType.INCOME, LedgerEntryType.ADJUSTMENT_CREDIT, LedgerEntryType.TRANSFER_IN]:
            # Original credited the account; reversal must debit it
            if account.current_balance < orig.amount:
                return False, "Cannot reverse: Account balance is less than reversed amount."
            account.current_balance -= orig.amount
            account.save()
            rev_type = LedgerEntryType.REVERSAL
        elif orig.entry_type in [LedgerEntryType.EXPENSE, LedgerEntryType.ADJUSTMENT_DEBIT, LedgerEntryType.TRANSFER_OUT]:
            # Original debited the account; reversal must credit it
            account.current_balance += orig.amount
            account.save()
            rev_type = LedgerEntryType.REVERSAL
        else:
            return False, "Cannot reverse a reversal entry."

        reversal = LedgerEntry.objects.create(
            entry_date=today,
            entry_type=rev_type,
            account=account,
            amount=orig.amount,
            balance_after=account.current_balance,
            description=f"Reversal of {orig.entry_id}: {reason}",
            reversal_of=orig,
            posted_by=user
        )

        orig.is_reversed = True
        orig.save(update_fields=["is_reversed"])

        AuditLog.objects.create(
            user=user,
            action="LEDGER_REVERSAL",
            target_model="LedgerEntry",
            target_id=orig.entry_id,
            details=f"Reversed {orig.entry_id} (₹{orig.amount}). Reason: {reason}"
        )

    return True, f"Reversal recorded with ID {reversal.entry_id}"
