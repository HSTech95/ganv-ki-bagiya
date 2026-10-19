from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser, UserRole
from apps.donors.models import Donor
from apps.donations.models import Donation, DonationReceipt, PaymentMethod, PaymentStatus, DonationPurpose
from apps.finance.models import FundAccount, AccountType, LedgerEntry, LedgerEntryType


class DonationModelAndWorkflowTestCase(TestCase):
    def setUp(self):
        self.treasurer = CustomUser.objects.create_user(
            username="test_treasurer",
            email="treasurer@test.com",
            password="Password@123",
            role=UserRole.TREASURER,
            is_staff=True
        )
        self.bank_acc = FundAccount.objects.create(
            name="SBI Main Account",
            account_type=AccountType.BANK,
            account_number="1234567890",
            current_balance=Decimal("10000.00"),
            is_active=True
        )
        self.donor = Donor.objects.create(
            name="Rahim Khan",
            phone="9876543210",
            email="rahim@example.com",
            address="Ward 4, Rampur",
            is_anonymous=False
        )

    def test_donation_creation_and_receipt_number(self):
        donation = Donation.objects.create(
            donor=self.donor,
            donor_name=self.donor.name,
            donor_phone=self.donor.phone,
            amount=Decimal("5000.00"),
            purpose=DonationPurpose.TREE_PLANTATION,
            payment_method=PaymentMethod.BANK_TRANSFER,
            payment_status=PaymentStatus.PENDING,
            donation_date=date.today(),
            recorded_by=self.treasurer
        )
        self.assertTrue(donation.donation_id.startswith("GKB-DON-"))
        self.assertTrue(donation.receipt_number.startswith("RCPT-"))
        self.assertEqual(donation.amount, Decimal("5000.00"))
        self.assertFalse(donation.is_posted_to_ledger)

    def test_anonymous_donation_privacy(self):
        anon_donor = Donor.objects.create(
            name="Secret Well-wisher",
            phone="9123456789",
            is_anonymous=True
        )
        donation = Donation.objects.create(
            donor=anon_donor,
            donor_name=anon_donor.name,
            donor_phone=anon_donor.phone,
            amount=Decimal("2000.00"),
            purpose=DonationPurpose.GENERAL_FUND,
            is_anonymous=True,
            payment_status=PaymentStatus.CONFIRMED,
            destination_account=self.bank_acc
        )
        self.assertEqual(donation.public_donor_name, "गुमनाम दानदाता (Anonymous)")
        self.assertTrue("*" in donation.masked_phone)
        self.assertEqual(donation.masked_phone, "91******89")

    def test_post_to_ledger_updates_account_balance(self):
        initial_balance = self.bank_acc.current_balance
        donation = Donation.objects.create(
            donor=self.donor,
            donor_name=self.donor.name,
            donor_phone=self.donor.phone,
            amount=Decimal("3000.00"),
            purpose=DonationPurpose.GARDEN_DEV,
            payment_method=PaymentMethod.BANK_TRANSFER,
            payment_status=PaymentStatus.CONFIRMED,
            destination_account=self.bank_acc,
            recorded_by=self.treasurer
        )

        success, msg = donation.post_to_ledger(user=self.treasurer)
        self.assertTrue(success)
        self.assertTrue(donation.is_posted_to_ledger)

        # Refresh account from DB
        self.bank_acc.refresh_from_db()
        self.assertEqual(self.bank_acc.current_balance, initial_balance + Decimal("3000.00"))

        # Verify ledger entry
        ledger_entry = LedgerEntry.objects.filter(reference_donation=donation).first()
        self.assertIsNotNone(ledger_entry)
        self.assertEqual(ledger_entry.amount, Decimal("3000.00"))
        self.assertEqual(ledger_entry.entry_type, LedgerEntryType.INCOME)
        self.assertEqual(ledger_entry.balance_after, self.bank_acc.current_balance)

        # Verify digital receipt
        receipt = DonationReceipt.objects.filter(donation=donation).first()
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.receipt_number, donation.receipt_number)

    def test_duplicate_ledger_posting_prevention(self):
        donation = Donation.objects.create(
            donor=self.donor,
            donor_name=self.donor.name,
            donor_phone=self.donor.phone,
            amount=Decimal("1500.00"),
            purpose=DonationPurpose.KABRISTAN_MAINTENANCE,
            payment_status=PaymentStatus.CONFIRMED,
            destination_account=self.bank_acc
        )
        success1, _ = donation.post_to_ledger(user=self.treasurer)
        self.assertTrue(success1)

        # Second attempt must fail
        success2, err = donation.post_to_ledger(user=self.treasurer)
        self.assertFalse(success2)
        self.assertIn("Already posted", err)


class PublicDonationFlowTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.bank_acc = FundAccount.objects.create(
            name="General Bank Account",
            account_type=AccountType.BANK,
            current_balance=Decimal("50000.00"),
            is_active=True
        )

    def test_public_donation_submission(self):
        response = self.client.post(reverse("donations:donate"), {
            "donor_name": "Tariq Mahmood",
            "donor_phone": "9988776655",
            "donor_email": "tariq@example.com",
            "amount": "2500",
            "purpose": DonationPurpose.GENERAL_FUND,
            "payment_method": PaymentMethod.UPI_QR,
            "message": "शुभकामनाएं"
        })
        self.assertEqual(response.status_code, 302)
        donation = Donation.objects.filter(donor_phone="9988776655").first()
        self.assertIsNotNone(donation)
        self.assertEqual(donation.amount, Decimal("2500.00"))
        self.assertEqual(donation.payment_status, PaymentStatus.PENDING)
