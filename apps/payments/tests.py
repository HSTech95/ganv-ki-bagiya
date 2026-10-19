import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser, UserRole
from apps.donors.models import Donor
from apps.donations.models import Donation, PaymentMethod, PaymentStatus, DonationPurpose
from apps.finance.models import FundAccount, AccountType
from apps.payments.models import PaymentTransaction, UPIReconciliationRecord
from apps.payments.views import verify_razorpay_signature


class PaymentWebhookAndReconciliationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.treasurer = CustomUser.objects.create_user(
            username="test_treasurer_payments",
            email="treasurer_pay@bagiya.org",
            password="Password@123",
            role=UserRole.TREASURER,
            is_staff=True
        )
        self.online_account = FundAccount.objects.create(
            name="Online Gateway Account",
            account_type=AccountType.ONLINE,
            current_balance=Decimal("20000.00"),
            is_active=True
        )
        self.bank_account = FundAccount.objects.create(
            name="SBI Bank Account",
            account_type=AccountType.BANK,
            current_balance=Decimal("50000.00"),
            is_active=True
        )
        self.donor = Donor.objects.create(name="Saleem Ansari", phone="9898989898")

    def test_razorpay_signature_verification(self):
        secret = "secret_key_123"
        order_id = "order_998877"
        payment_id = "pay_112233"
        import hmac
        import hashlib
        valid_sig = hmac.new(
            secret.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        self.assertTrue(verify_razorpay_signature(order_id, payment_id, valid_sig, secret))
        self.assertFalse(verify_razorpay_signature(order_id, payment_id, "invalid_sig", secret))

    def test_webhook_captured_and_idempotent_ledger_posting(self):
        donation = Donation.objects.create(
            donor=self.donor,
            donor_name=self.donor.name,
            donor_phone=self.donor.phone,
            amount=Decimal("5000.00"),
            purpose=DonationPurpose.GARDEN_DEV,
            payment_method=PaymentMethod.ONLINE_GATEWAY,
            payment_status=PaymentStatus.PENDING
        )

        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_001",
                        "order_id": "order_test_001",
                        "amount": 500000,
                        "notes": {"donation_id": donation.donation_id}
                    }
                }
            }
        }

        # First webhook call
        response = self.client.post(
            reverse("payments:razorpay_webhook"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        donation.refresh_from_db()
        self.assertEqual(donation.payment_status, PaymentStatus.CONFIRMED)
        self.assertTrue(donation.is_posted_to_ledger)

        initial_balance = self.online_account.current_balance
        self.online_account.refresh_from_db()
        self.assertEqual(self.online_account.current_balance, initial_balance + Decimal("5000.00"))

        # Duplicate webhook call (Idempotency test)
        response_dup = self.client.post(
            reverse("payments:razorpay_webhook"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response_dup.status_code, 200)
        self.assertIn("already processed", response_dup.content.decode("utf-8"))

        # Account balance must NOT be incremented a second time!
        balance_after_dup = self.online_account.current_balance
        self.online_account.refresh_from_db()
        self.assertEqual(self.online_account.current_balance, balance_after_dup)

    def test_upi_reconciliation_auto_matching(self):
        utr = "987654321012"
        donation = Donation.objects.create(
            donor=self.donor,
            donor_name=self.donor.name,
            donor_phone=self.donor.phone,
            amount=Decimal("3500.00"),
            purpose=DonationPurpose.KABRISTAN_MAINTENANCE,
            payment_method=PaymentMethod.UPI_QR,
            payment_status=PaymentStatus.PENDING,
            transaction_reference=utr,
            destination_account=self.bank_account
        )

        # Create bank statement record with matching UTR and amount
        record = UPIReconciliationRecord.objects.create(
            bank_statement_date=timezone.now().date(),
            utr_number=utr,
            amount=Decimal("3500.00"),
            payer_details="UPI/987654321012/Saleem",
            is_matched=False
        )

        self.client.force_login(self.treasurer)
        response = self.client.post(reverse("payments:dashboard_upi_auto_match"))
        self.assertEqual(response.status_code, 302)

        record.refresh_from_db()
        self.assertTrue(record.is_matched)
        self.assertEqual(record.matched_donation, donation)

        donation.refresh_from_db()
        self.assertEqual(donation.payment_status, PaymentStatus.CONFIRMED)
        self.assertTrue(donation.is_posted_to_ledger)
