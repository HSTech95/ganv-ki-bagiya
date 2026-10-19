import uuid
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser
from apps.projects.models import Project
from apps.finance.models import FundAccount, LedgerEntry, LedgerEntryType


class ExpenseCategory(models.TextChoices):
    GARDEN_MAINTENANCE = "GARDEN_MAINTENANCE", _("बगिया की देखरेख (Garden Maintenance)")
    TREE_PLANTATION = "TREE_PLANTATION", _("पेड़-पौधे व खाद (Plants & Seeds)")
    WATER_ELECTRICITY = "WATER_ELECTRICITY", _("पानी, बोरिंग और बिजली (Water & Light)")
    LABOUR_CHARGES = "LABOUR_CHARGES", _("मजदूरी व मिस्त्री खर्च (Labour Charges)")
    CONSTRUCTION = "CONSTRUCTION", _("निर्माण सामान - ईंट, सीमेंट, रेत (Materials)")
    BOUNDARY_WALL = "BOUNDARY_WALL", _("चारदीवारी व लोहे का गेट (Boundary & Gate)")
    KABRISTAN_MAINTENANCE = "KABRISTAN_MAINTENANCE", _("कब्रिस्तान की सफाई व देखरेख (Kabristan Care)")
    TOOLS_EQUIPMENT = "TOOLS_EQUIPMENT", _("औजार व सामान - पाइप, फावड़ा (Tools)")
    COMMUNITY_EVENTS = "COMMUNITY_EVENTS", _("बैठक व कार्यक्रम खर्च (Meetings & Events)")
    ADMINISTRATIVE = "ADMINISTRATIVE", _("रसीद बुक व ऑफिस खर्च (Office & Stationery)")
    MISCELLANEOUS = "MISCELLANEOUS", _("अन्य छोटे-मोटे खर्च (Miscellaneous)")


class ExpenseApprovalStatus(models.TextChoices):
    DRAFT = "DRAFT", _("कच्चा ड्राफ्ट (Draft)")
    SUBMITTED = "SUBMITTED", _("मंजूरी के लिए भेजा (Submitted)")
    APPROVED = "APPROVED", _("कमेटी द्वारा मंजूर (Approved)")
    REJECTED = "REJECTED", _("नामंजूर (Rejected)")


class ExpensePaymentStatus(models.TextChoices):
    UNPAID = "UNPAID", _("भुगतान बाकी (Unpaid)")
    PAID = "PAID", _("भुगतान हो गया (Paid)")


class Expense(models.Model):
    expense_id = models.CharField(max_length=35, unique=True, editable=False)
    expense_date = models.DateField(default=timezone.now, verbose_name=_("खर्च की तारीख (Expense Date)"))
    category = models.CharField(
        max_length=35,
        choices=ExpenseCategory.choices,
        default=ExpenseCategory.GARDEN_MAINTENANCE,
        verbose_name=_("खर्च की श्रेणी (Category)")
    )
    description = models.CharField(max_length=255, verbose_name=_("खर्च का विवरण (Description)"))
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("खर्च की रकम (Amount ₹)")
    )
    vendor_name = models.CharField(max_length=150, verbose_name=_("दुकानदार / मिस्त्री / मजदूर का नाम (Payee)"))
    vendor_phone = models.CharField(max_length=20, blank=True, verbose_name=_("फोन नंबर (Phone)"))
    bill_number = models.CharField(max_length=100, blank=True, verbose_name=_("बिल / पर्ची नंबर (Bill No.)"))
    bill_date = models.DateField(null=True, blank=True, verbose_name=_("बिल की तारीख (Bill Date)"))
    bill_file = models.FileField(
        upload_to="bills/",
        blank=True,
        null=True,
        verbose_name=_("बिल / पक्की रसीद की फ़ोटो (Bill File)")
    )
    related_project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="expenses",
        verbose_name=_("संबंधित प्रोजेक्ट (Project)")
    )
    
    # Workflow
    approval_status = models.CharField(
        max_length=20,
        choices=ExpenseApprovalStatus.choices,
        default=ExpenseApprovalStatus.DRAFT,
        verbose_name=_("Approval Status")
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name="created_expenses",
        verbose_name=_("Recorded By")
    )
    approved_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_expenses",
        verbose_name=_("Reviewed / Approved By")
    )
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Approval Timestamp"))
    approval_notes = models.TextField(blank=True, verbose_name=_("Approval / Rejection Remarks"))
    
    # Payment execution
    payment_status = models.CharField(
        max_length=20,
        choices=ExpensePaymentStatus.choices,
        default=ExpensePaymentStatus.UNPAID,
        verbose_name=_("Payment Status")
    )
    payment_method = models.CharField(
        max_length=25,
        blank=True,
        verbose_name=_("Payment Mode (Cash/Bank/UPI)")
    )
    paid_from_account = models.ForeignKey(
        FundAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses_paid",
        verbose_name=_("Paid From Account")
    )
    paid_date = models.DateField(null=True, blank=True, verbose_name=_("Payment Execution Date"))
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Payment Reference (Cheque No. / UTR / Cash Voucher)")
    )
    is_posted_to_ledger = models.BooleanField(
        default=False,
        verbose_name=_("Posted to Financial Ledger")
    )
    notes = models.TextField(blank=True, verbose_name=_("Internal Notes"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")

    def save(self, *args, **kwargs):
        if not self.expense_id:
            year_month = self.expense_date.strftime("%Y%m")
            short_uuid = uuid.uuid4().hex[:6].upper()
            self.expense_id = f"GKB-EXP-{year_month}-{short_uuid}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.expense_id}] ₹{self.amount} - {self.description} ({self.get_approval_status_display()})"

    def record_payment(self, account, method, reference, user, paid_date=None):
        """
        Atomically records payment of an approved expense.
        Reduces account balance, records an immutable ledger entry, and prevents double-posting.
        """
        if self.approval_status != ExpenseApprovalStatus.APPROVED:
            return False, "Expense must be approved by the committee before payment."
        if self.payment_status == ExpensePaymentStatus.PAID or self.is_posted_to_ledger:
            return False, "This expense is already marked as paid and posted to ledger."

        with transaction.atomic():
            account = FundAccount.objects.select_for_update().get(pk=account.pk)
            if account.current_balance < self.amount:
                return False, f"Insufficient funds in {account.name}. Available: ₹{account.current_balance}, Required: ₹{self.amount}"

            account.current_balance -= self.amount
            account.save()

            exec_date = paid_date or timezone.now().date()
            self.paid_from_account = account
            self.payment_method = method
            self.payment_reference = reference
            self.payment_status = ExpensePaymentStatus.PAID
            self.paid_date = exec_date
            self.is_posted_to_ledger = True
            self.save(update_fields=[
                "paid_from_account", "payment_method", "payment_reference",
                "payment_status", "paid_date", "is_posted_to_ledger"
            ])

            LedgerEntry.objects.create(
                entry_date=exec_date,
                entry_type=LedgerEntryType.EXPENSE,
                account=account,
                amount=self.amount,
                balance_after=account.current_balance,
                description=f"Paid to {self.vendor_name}: {self.description} ({self.get_category_display()})",
                reference_expense=self,
                posted_by=user
            )

            ExpenseApprovalLog.objects.create(
                expense=self,
                action="PAYMENT_RECORDED",
                user=user,
                comments=f"Paid ₹{self.amount} via {method} from {account.name}. Ref: {reference}"
            )

        return True, "Payment recorded and ledger updated successfully."


class ExpenseAttachment(models.Model):
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Expense")
    )
    file = models.FileField(upload_to="bills_and_receipts/", verbose_name=_("Attached File"))
    title = models.CharField(max_length=150, blank=True, verbose_name=_("Title / Description"))
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = _("Expense Attachment")
        verbose_name_plural = _("Expense Attachments")

    def __str__(self):
        return f"Attachment for {self.expense.expense_id} ({self.title or self.file.name})"


class ExpenseApprovalLog(models.Model):
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="approval_logs",
        verbose_name=_("Expense")
    )
    action = models.CharField(max_length=50, verbose_name=_("Action Taken"))
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        verbose_name=_("Action By")
    )
    comments = models.TextField(blank=True, verbose_name=_("Remarks / Reasons"))
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = _("Expense Approval Log")
        verbose_name_plural = _("Expense Approval Logs")

    def __str__(self):
        return f"{self.expense.expense_id} - {self.action} by {self.user.username} at {self.timestamp:%Y-%m-%d %H:%M}"
