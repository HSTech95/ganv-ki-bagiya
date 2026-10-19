from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import CustomUser, UserRole
from apps.donors.models import Donor
from apps.donations.models import Donation, PaymentStatus, DonationPurpose
from apps.expenses.models import Expense, ExpenseCategory, ExpenseApprovalStatus, ExpensePaymentStatus
from apps.finance.models import (
    FundAccount, AccountType, LedgerEntry, LedgerEntryType,
    DailyBalanceSnapshot, AccountTransfer
)
from apps.finance.services import (
    get_financial_summary, calculate_daily_balance,
    execute_account_transfer, reverse_ledger_entry
)


class FinanceAccountingAndLedgerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="treasurer_finance",
            email="fin@bagiya.org",
            password="Password@123",
            role=UserRole.TREASURER,
            is_staff=True
        )
        self.bank_account = FundAccount.objects.create(
            name="SBI Trust Account",
            account_type=AccountType.BANK,
            current_balance=Decimal("100000.00"),
            is_active=True
        )
        self.cash_account = FundAccount.objects.create(
            name="Cash Chest",
            account_type=AccountType.CASH,
            current_balance=Decimal("20000.00"),
            is_active=True
        )
        self.donor = Donor.objects.create(name="Donor A", phone="9000000001")

    def test_daily_balance_calculation_formula(self):
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Yesterday snapshot with 50,000 closing
        DailyBalanceSnapshot.objects.create(
            date=yesterday,
            opening_balance=Decimal("40000.00"),
            total_income=Decimal("15000.00"),
            total_expense=Decimal("5000.00"),
            closing_balance=Decimal("50000.00")
        )

        # Create today's income entry via Ledger
        LedgerEntry.objects.create(
            entry_date=today,
            entry_type=LedgerEntryType.INCOME,
            account=self.bank_account,
            amount=Decimal("25000.00"),
            balance_after=self.bank_account.current_balance + Decimal("25000.00"),
            description="Donation received",
            posted_by=self.user
        )

        # Create today's paid expense entry via Ledger
        LedgerEntry.objects.create(
            entry_date=today,
            entry_type=LedgerEntryType.EXPENSE,
            account=self.bank_account,
            amount=Decimal("10000.00"),
            balance_after=self.bank_account.current_balance + Decimal("15000.00"),
            description="Bricks purchase",
            posted_by=self.user
        )

        # Calculate today's snapshot
        snapshot = calculate_daily_balance(today)
        self.assertEqual(snapshot.opening_balance, Decimal("50000.00"))
        self.assertEqual(snapshot.total_income, Decimal("25000.00"))
        self.assertEqual(snapshot.total_expense, Decimal("10000.00"))
        # Closing = Opening (50000) + Income (25000) - Expense (10000) = 65000
        self.assertEqual(snapshot.closing_balance, Decimal("65000.00"))

    def test_internal_account_transfer_without_income_expense_inflation(self):
        initial_bank = self.bank_account.current_balance
        initial_cash = self.cash_account.current_balance
        transfer_amt = Decimal("15000.00")

        success, msg = execute_account_transfer(
            from_account=self.bank_account,
            to_account=self.cash_account,
            amount=transfer_amt,
            reason="Cash withdrawal for daily labour payments",
            user=self.user
        )
        self.assertTrue(success)

        self.bank_account.refresh_from_db()
        self.cash_account.refresh_from_db()

        self.assertEqual(self.bank_account.current_balance, initial_bank - transfer_amt)
        self.assertEqual(self.cash_account.current_balance, initial_cash + transfer_amt)

        # Total combined book balance must remain identical
        self.assertEqual(
            self.bank_account.current_balance + self.cash_account.current_balance,
            initial_bank + initial_cash
        )

        # Check ledger entries for transfer out and transfer in
        out_entry = LedgerEntry.objects.filter(
            account=self.bank_account,
            entry_type=LedgerEntryType.TRANSFER_OUT
        ).first()
        in_entry = LedgerEntry.objects.filter(
            account=self.cash_account,
            entry_type=LedgerEntryType.TRANSFER_IN
        ).first()
        self.assertIsNotNone(out_entry)
        self.assertIsNotNone(in_entry)
        self.assertEqual(out_entry.amount, transfer_amt)
        self.assertEqual(in_entry.amount, transfer_amt)

    def test_transfer_fails_when_insufficient_funds(self):
        excessive_amount = Decimal("200000.00")  # Bank only has 100,000
        success, msg = execute_account_transfer(
            from_account=self.bank_account,
            to_account=self.cash_account,
            amount=excessive_amount,
            reason="Exceeding funds test",
            user=self.user
        )
        self.assertFalse(success)
        self.assertIn("Insufficient balance", msg)

    def test_ledger_reversal_workflow(self):
        initial_balance = self.bank_account.current_balance
        entry = LedgerEntry.objects.create(
            entry_date=date.today(),
            entry_type=LedgerEntryType.INCOME,
            account=self.bank_account,
            amount=Decimal("5000.00"),
            balance_after=initial_balance + Decimal("5000.00"),
            description="Erroneous deposit",
            posted_by=self.user
        )
        # Update account balance to simulate original posting
        self.bank_account.current_balance += Decimal("5000.00")
        self.bank_account.save()

        # Execute reversal
        success, msg = reverse_ledger_entry(
            entry_id=entry.entry_id,
            user=self.user,
            reason="Wrong donor deposit credited"
        )
        self.assertTrue(success)

        entry.refresh_from_db()
        self.assertTrue(entry.is_reversed)

        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.current_balance, initial_balance)

        # Reversing a reversed entry must fail
        success2, msg2 = reverse_ledger_entry(
            entry_id=entry.entry_id,
            user=self.user,
            reason="Double reversal attempt"
        )
        self.assertFalse(success2)
        self.assertIn("already been reversed", msg2)

    def test_financial_summary_aggregation(self):
        summary = get_financial_summary()
        self.assertEqual(
            summary["current_book_balance"],
            self.bank_account.current_balance + self.cash_account.current_balance
        )
        self.assertEqual(summary["cash_balance"], self.cash_account.current_balance)
        self.assertEqual(summary["bank_balance"], self.bank_account.current_balance)
