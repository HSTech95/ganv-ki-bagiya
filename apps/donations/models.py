import uuid
from decimal import Decimal
# pyrefly: ignore [missing-import]
from django.db import models, transaction
# pyrefly: ignore [missing-import]
from django.utils import timezone
# pyrefly: ignore [missing-import]
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser
from apps.donors.models import Donor
from apps.projects.models import Project
from apps.finance.models import FundAccount, LedgerEntry, LedgerEntryType


class DonationPurpose(models.TextChoices):
    GENERAL_FUND = "GENERAL_FUND", _("आम फंड / सामान्य खर्च (General Fund)")
    GARDEN_DEV = "GARDEN_DEV", _("बगिया विकास (Garden Work)")
    TREE_PLANTATION = "TREE_PLANTATION", _("पेड़-पौधे लगाना (Tree Plantation)")
    GARDEN_MAINTENANCE = "GARDEN_MAINTENANCE", _("बगिया की देखरेख (Garden Maintenance)")
    KABRISTAN_MAINTENANCE = "KABRISTAN_MAINTENANCE", _("कब्रिस्तान की देखरेख व सफाई (Kabristan Care)")
    BOUNDARY_WALL = "BOUNDARY_WALL", _("चारदीवारी और मेन गेट (Boundary & Gate)")
    WATER_ELECTRICITY = "WATER_ELECTRICITY", _("पानी, बोरिंग और लाइट (Water & Light)")
    OTHER = "OTHER", _("अन्य ज़रूरी काम (Other Projects)")


class PaymentMethod(models.TextChoices):
    CASH = "CASH", _("नकद (Cash)")
    UPI_QR = "UPI_QR", _("UPI / क्यूआर कोड (UPI QR)")
    BANK_TRANSFER = "BANK_TRANSFER", _("सीधे बैंक खाता (Bank Transfer)")
    ONLINE_GATEWAY = "ONLINE_GATEWAY", _("ऑनलाइन पेमेंट (Online Payment)")


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", _("जांच बाकी (Pending Verification)")
    CONFIRMED = "CONFIRMED", _("पक्का / सत्यापित (Confirmed)")
    FAILED = "FAILED", _("असफल (Failed)")
    REFUNDED = "REFUNDED", _("वापस किया गया (Refunded)")


class Donation(models.Model):
    donation_id = models.CharField(max_length=35, unique=True, editable=False)
    receipt_number = models.CharField(max_length=35, unique=True, blank=True)
    donor = models.ForeignKey(
        Donor,
        on_delete=models.CASCADE,
        related_name="donations",
        verbose_name=_("दानदाता रिकॉर्ड (Donor Record)")
    )
    donor_name = models.CharField(max_length=150, verbose_name=_("दानदाता का नाम (Donor Name)"))
    donor_phone = models.CharField(max_length=20, blank=True, verbose_name=_("मोबाइल नंबर (Donor Phone)"))
    donor_email = models.EmailField(blank=True, verbose_name=_("ईमेल (Donor Email)"))
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name=_("गुप्त दान रखें (Anonymous)")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("दान की रकम (Amount ₹)")
    )
    purpose = models.CharField(
        max_length=30,
        choices=DonationPurpose.choices,
        default=DonationPurpose.GENERAL_FUND,
        verbose_name=_("दान किस काम के लिए (Purpose)")
    )
    related_project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="donations",
        verbose_name=_("प्रोजेक्ट (Designated Project)")
    )
    payment_method = models.CharField(
        max_length=25,
        choices=PaymentMethod.choices,
        default=PaymentMethod.UPI_QR,
        verbose_name=_("भुगतान का तरीका (Payment Method)")
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_("पेमेंट की स्थिति (Status)")
    )
    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("UTR / बैंक ट्रांजैक्शन नंबर (Ref No.)"),
        help_text=_("12 अंकों का यूपीआई UTR या बैंक रेफरेंस नंबर")
    )
    destination_account = models.ForeignKey(
        FundAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="donations_received",
        verbose_name=_("जमा खाता (Deposited Account)")
    )
    is_posted_to_ledger = models.BooleanField(
        default=False,
        verbose_name=_("रजिस्टर में दर्ज (Posted to Ledger)")
    )
    donation_date = models.DateField(default=timezone.now, verbose_name=_("दान की तारीख (Date)"))
    message = models.TextField(blank=True, verbose_name=_("Donor Message / Blessing"))
    payment_proof = models.FileField(
        upload_to="donation_proofs/",
        blank=True,
        null=True,
        verbose_name=_("Receipt / UPI Slip Screenshot")
    )
    recorded_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recorded_donations",
        verbose_name=_("Recorded By")
    )
    verified_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_donations",
        verbose_name=_("Verified By")
    )
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Verification Timestamp"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-donation_date", "-created_at"]
        verbose_name = _("Donation")
        verbose_name_plural = _("Donations")

    def save(self, *args, **kwargs):
        if not self.donation_id:
            year_month = self.donation_date.strftime("%Y%m")
            short_uuid = uuid.uuid4().hex[:6].upper()
            self.donation_id = f"GKB-DON-{year_month}-{short_uuid}"
        if not self.receipt_number:
            year_month = self.donation_date.strftime("%Y%m")
            short_uuid = uuid.uuid4().hex[:6].upper()
            self.receipt_number = f"RCPT-{year_month}-{short_uuid}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.donation_id}] ₹{self.amount} - {self.public_donor_name} ({self.get_payment_status_display()})"

    @property
    def public_donor_name(self):
        if self.is_anonymous:
            return "गुमनाम दानदाता (Anonymous)"
        return self.donor_name

    @property
    def masked_phone(self):
        if not self.donor_phone or len(self.donor_phone) < 6:
            return "******"
        return f"{self.donor_phone[:2]}******{self.donor_phone[-2:]}"

    def post_to_ledger(self, user=None):
        """
        Atomically post confirmed donation to the financial ledger and increment fund account.
        Enforces immutable ledger integrity.
        """
        if self.is_posted_to_ledger:
            return False, "Already posted to ledger."
        if self.payment_status != PaymentStatus.CONFIRMED:
            return False, "Cannot post unconfirmed donation to ledger."
        if not self.destination_account:
            # Assign appropriate default account
            if self.payment_method == PaymentMethod.CASH:
                account = FundAccount.objects.filter(account_type="CASH", is_active=True).first()
            elif self.payment_method in [PaymentMethod.ONLINE_GATEWAY, PaymentMethod.UPI_QR]:
                account = FundAccount.objects.filter(account_type__in=["UPI", "ONLINE"], is_active=True).first()
            else:
                account = FundAccount.objects.filter(account_type="BANK", is_active=True).first()
            if not account:
                account = FundAccount.objects.filter(is_active=True).first()
            self.destination_account = account

        with transaction.atomic():
            # Concurrency control: select_for_update on account
            account = FundAccount.objects.select_for_update().get(pk=self.destination_account.pk)
            account.current_balance += self.amount
            account.save()

            posting_user = user or self.verified_by or self.recorded_by
            if not posting_user:
                posting_user = (
                    CustomUser.objects.filter(is_superuser=True).first()
                    or CustomUser.objects.filter(is_staff=True).first()
                    or CustomUser.objects.first()
                )
            if not posting_user:
                posting_user = CustomUser.objects.create_user(
                    username="system_auto",
                    email="system@ganvkibagiya.org",
                    role="SUPER_ADMIN",
                    is_staff=True,
                    is_superuser=True
                )

            ledger = LedgerEntry.objects.create(
                entry_date=self.donation_date,
                entry_type=LedgerEntryType.INCOME,
                account=account,
                amount=self.amount,
                balance_after=account.current_balance,
                description=f"Donation received from {self.donor_name} ({self.get_purpose_display()})",
                reference_donation=self,
                posted_by=posting_user
            )

            self.is_posted_to_ledger = True
            self.save(update_fields=["is_posted_to_ledger", "destination_account"])

            # Create or update receipt
            DonationReceipt.objects.get_or_create(
                donation=self,
                defaults={"receipt_number": self.receipt_number, "issued_by": posting_user}
            )

        return True, "Successfully posted to ledger."


class DonationReceipt(models.Model):
    donation = models.OneToOneField(
        Donation,
        on_delete=models.CASCADE,
        related_name="receipt",
        verbose_name=_("Donation")
    )
    receipt_number = models.CharField(max_length=35, unique=True, verbose_name=_("Receipt Number"))
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Issued At"))
    issued_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Issued By")
    )
    pdf_file = models.FileField(
        upload_to="receipts/",
        blank=True,
        null=True,
        verbose_name=_("Receipt PDF")
    )

    class Meta:
        ordering = ["-issued_at"]
        verbose_name = _("Donation Receipt")
        verbose_name_plural = _("Donation Receipts")

    def __str__(self):
        return f"Receipt {self.receipt_number} for {self.donation.donation_id}"
