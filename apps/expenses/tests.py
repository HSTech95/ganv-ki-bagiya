from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import CustomUser, UserRole
from apps.expenses.models import (
    Expense, ExpenseCategory, ExpenseApprovalStatus,
    ExpensePaymentStatus, ExpenseApprovalLog
)
from apps.finance.models import FundAccount, AccountType, LedgerEntry, LedgerEntryType
from apps.projects.models import Project, ProjectStatus


class ExpenseLifecycleAndPaymentTestCase(TestCase):
    def setUp(self):
        self.manager = CustomUser.objects.create_user(
            username="test_manager",
            email="manager@test.com",
            password="Password@123",
            role=UserRole.PROJECT_MANAGER,
            is_staff=True
        )
        self.president = CustomUser.objects.create_user(
            username="test_president",
            email="president@test.com",
            password="Password@123",
            role=UserRole.PRESIDENT,
            is_staff=True
        )
        self.treasurer = CustomUser.objects.create_user(
            username="test_treasurer_exp",
            email="treasurer_exp@test.com",
            password="Password@123",
            role=UserRole.TREASURER,
            is_staff=True
        )
        self.bank_account = FundAccount.objects.create(
            name="SBI Bagiya Main Account",
            account_type=AccountType.BANK,
            current_balance=Decimal("50000.00"),
            is_active=True
        )
        self.project = Project.objects.create(
            name="Tree Plantation Phase 1",
            slug="tree-plantation-phase-1",
            description="Phase 1 tree plantation",
            estimated_budget=Decimal("30000.00"),
            start_date=date.today(),
            status=ProjectStatus.ACTIVE,
            manager=self.manager
        )

    def test_expense_creation_and_approval_workflow(self):
        expense = Expense.objects.create(
            category=ExpenseCategory.TREE_PLANTATION,
            description="Purchase of 50 Neem & Peepal Saplings",
            amount=Decimal("7500.00"),
            vendor_name="Rampur Nursery",
            related_project=self.project,
            approval_status=ExpenseApprovalStatus.SUBMITTED,
            created_by=self.manager
        )
        self.assertTrue(expense.expense_id.startswith("GKB-EXP-"))
        self.assertEqual(expense.payment_status, ExpensePaymentStatus.UNPAID)
        self.assertFalse(expense.is_posted_to_ledger)

        # Committee President approves expense
        expense.approval_status = ExpenseApprovalStatus.APPROVED
        expense.approved_by = self.president
        expense.approval_date = timezone.now()
        expense.save()

        # At this stage, payment has not been made, so balance must remain unchanged!
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.current_balance, Decimal("50000.00"))
        self.assertFalse(expense.is_posted_to_ledger)

    def test_payment_execution_atomically_updates_ledger_and_balance(self):
        initial_balance = self.bank_account.current_balance
        expense_amt = Decimal("12000.00")

        expense = Expense.objects.create(
            category=ExpenseCategory.CONSTRUCTION,
            description="Bricks for boundary wall",
            amount=expense_amt,
            vendor_name="Shree Ram Brick Kiln",
            related_project=self.project,
            approval_status=ExpenseApprovalStatus.APPROVED,
            approved_by=self.president,
            created_by=self.manager
        )

        success, msg = expense.record_payment(
            account=self.bank_account,
            method="Cheque",
            reference="CHQ-981023",
            user=self.treasurer,
            paid_date=date.today()
        )
        self.assertTrue(success)

        # Verify expense status
        expense.refresh_from_db()
        self.assertEqual(expense.payment_status, ExpensePaymentStatus.PAID)
        self.assertTrue(expense.is_posted_to_ledger)
        self.assertEqual(expense.paid_from_account, self.bank_account)

        # Verify fund account balance decreased
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.current_balance, initial_balance - expense_amt)

        # Verify immutable ledger entry
        ledger_entry = LedgerEntry.objects.filter(reference_expense=expense).first()
        self.assertIsNotNone(ledger_entry)
        self.assertEqual(ledger_entry.entry_type, LedgerEntryType.EXPENSE)
        self.assertEqual(ledger_entry.amount, expense_amt)
        self.assertEqual(ledger_entry.balance_after, self.bank_account.current_balance)

        # Verify audit log
        log = ExpenseApprovalLog.objects.filter(expense=expense, action="PAYMENT_RECORDED").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.treasurer)

    def test_cannot_pay_unapproved_expense(self):
        draft_expense = Expense.objects.create(
            category=ExpenseCategory.MISCELLANEOUS,
            description="Unapproved stationery expense",
            amount=Decimal("500.00"),
            vendor_name="Stationery Store",
            approval_status=ExpenseApprovalStatus.DRAFT,
            created_by=self.manager
        )
        success, msg = draft_expense.record_payment(
            account=self.bank_account,
            method="Cash",
            reference="VOUCH-01",
            user=self.treasurer
        )
        self.assertFalse(success)
        self.assertIn("must be approved", msg)

    def test_payment_fails_when_account_has_insufficient_funds(self):
        large_expense = Expense.objects.create(
            category=ExpenseCategory.CONSTRUCTION,
            description="Heavy machinery hire",
            amount=Decimal("90000.00"),  # Account only has 50,000
            vendor_name="Heavy Machinery Services",
            approval_status=ExpenseApprovalStatus.APPROVED,
            approved_by=self.president,
            created_by=self.manager
        )
        success, msg = large_expense.record_payment(
            account=self.bank_account,
            method="Bank Transfer",
            reference="UTR-8877",
            user=self.treasurer
        )
        self.assertFalse(success)
        self.assertIn("Insufficient funds", msg)
