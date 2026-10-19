from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import CustomUser, UserRole
from apps.donors.models import Donor
from apps.donations.models import Donation, PaymentMethod, PaymentStatus, DonationPurpose
from apps.expenses.models import Expense, ExpenseCategory, ExpenseApprovalStatus, ExpensePaymentStatus
from apps.finance.models import FundAccount, AccountType, LedgerEntry, LedgerEntryType


class ReportsAndExportsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.treasurer = CustomUser.objects.create_user(
            username="test_treasurer_reports",
            email="treasurer_rep@bagiya.org",
            password="Password@123",
            role=UserRole.TREASURER,
            is_staff=True
        )
        self.public_user = CustomUser.objects.create_user(
            username="public_test",
            email="pub@test.com",
            password="Password@123",
            role=UserRole.PUBLIC,
            is_staff=False
        )
        self.bank_account = FundAccount.objects.create(
            name="SBI Bank Account",
            account_type=AccountType.BANK,
            current_balance=Decimal("75000.00"),
            is_active=True
        )
        self.donor = Donor.objects.create(name="Abdul Wahid", phone="9871234560")
        self.donation = Donation.objects.create(
            donor=self.donor,
            donor_name=self.donor.name,
            donor_phone=self.donor.phone,
            amount=Decimal("10000.00"),
            purpose=DonationPurpose.GARDEN_DEV,
            payment_status=PaymentStatus.CONFIRMED,
            destination_account=self.bank_account
        )
        self.expense = Expense.objects.create(
            category=ExpenseCategory.GARDEN_MAINTENANCE,
            description="Grass cutting and maintenance",
            amount=Decimal("3000.00"),
            vendor_name="Worker Ramu",
            approval_status=ExpenseApprovalStatus.APPROVED,
            payment_status=ExpensePaymentStatus.PAID,
            paid_from_account=self.bank_account,
            created_by=self.treasurer
        )

    def test_unauthorized_user_cannot_access_reports_index(self):
        self.client.force_login(self.public_user)
        response = self.client.get(reverse("reports:index"))
        self.assertEqual(response.status_code, 302)

    def test_treasurer_can_access_reports_index(self):
        self.client.force_login(self.treasurer)
        response = self.client.get(reverse("reports:index"))
        self.assertEqual(response.status_code, 200)

    def test_export_donations_csv(self):
        self.client.force_login(self.treasurer)
        response = self.client.get(reverse("reports:donations_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("Donation ID", content)
        self.assertIn(self.donor.name, content)
        self.assertIn("10000.00", content)

    def test_export_donations_excel(self):
        self.client.force_login(self.treasurer)
        response = self.client.get(reverse("reports:donations_excel"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])

    def test_export_expenses_csv(self):
        self.client.force_login(self.treasurer)
        response = self.client.get(reverse("reports:expenses_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("Expense ID", content)
        self.assertIn("Grass cutting and maintenance", content)

    def test_export_expenses_excel(self):
        self.client.force_login(self.treasurer)
        response = self.client.get(reverse("reports:expenses_excel"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])

    def test_export_financial_statement_pdf(self):
        self.client.force_login(self.treasurer)
        response = self.client.get(reverse("reports:financial_statement_pdf"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
