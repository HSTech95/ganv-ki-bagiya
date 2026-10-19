from decimal import Decimal
from django.test import TestCase
from apps.donors.models import Donor
from apps.donations.models import Donation, PaymentStatus, DonationPurpose


class DonorsTestCase(TestCase):
    def setUp(self):
        self.donor = Donor.objects.create(
            name="Shahid Afridi",
            phone="9876123450",
            email="shahid@example.com",
            address="Mohalla Ansariyan",
            is_anonymous=False
        )

    def test_donor_properties_and_history(self):
        Donation.objects.create(
            donor=self.donor,
            donor_name=self.donor.name,
            donor_phone=self.donor.phone,
            amount=Decimal("4000.00"),
            purpose=DonationPurpose.TREE_PLANTATION,
            payment_status=PaymentStatus.CONFIRMED
        )
        Donation.objects.create(
            donor=self.donor,
            donor_name=self.donor.name,
            donor_phone=self.donor.phone,
            amount=Decimal("6000.00"),
            purpose=DonationPurpose.KABRISTAN_MAINTENANCE,
            payment_status=PaymentStatus.CONFIRMED
        )
        self.assertEqual(self.donor.donations.count(), 2)
        total_donated = sum(d.amount for d in self.donor.donations.filter(payment_status=PaymentStatus.CONFIRMED))
        self.assertEqual(total_donated, Decimal("10000.00"))
