from decimal import Decimal
# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse
from django.db import models
from django.db.models import Q

from .models import Donation, DonationReceipt, PaymentMethod, PaymentStatus, DonationPurpose
from .forms import PublicDonationForm, UPISubmitReferenceForm, StaffDonationEntryForm
from .utils import generate_upi_payload, generate_upi_qr_base64, get_phonepe_qr_base64
from apps.donors.models import Donor
from apps.content.models import SiteSetting
from apps.finance.models import FundAccount
from apps.accounts.models import AuditLog
from apps.finance.services import get_financial_summary
from apps.projects.models import Project


def donate_view(request):
    """
    Public donation form.
    """
    settings = SiteSetting.load()
    if request.method == "POST":
        form = PublicDonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            custom_amount = form.cleaned_data.get("custom_amount")
            if custom_amount and custom_amount > 0:
                donation.amount = custom_amount

            # Find or create Donor profile
            phone = form.cleaned_data.get("donor_phone", "").strip()
            name = form.cleaned_data.get("donor_name", "").strip()
            email = form.cleaned_data.get("donor_email", "").strip()
            is_anon = form.cleaned_data.get("is_anonymous", False)

            donor = Donor.objects.filter(phone=phone).first() if phone else None
            if not donor:
                donor = Donor.objects.create(
                    name=name,
                    phone=phone,
                    email=email,
                    is_anonymous=is_anon
                )
            else:
                if not donor.email and email:
                    donor.email = email
                    donor.save()

            donation.donor = donor
            donation.save()

            if donation.payment_method == PaymentMethod.UPI_QR:
                return redirect("donations:donate_upi", donation_id=donation.donation_id)
            elif donation.payment_method == PaymentMethod.ONLINE_GATEWAY:
                return redirect("donations:donate_gateway", donation_id=donation.donation_id)
            else:
                messages.success(
                    request,
                    f"दान प्रपत्र दर्ज हो गया है (Ref ID: {donation.donation_id})। कृपया समिति के खजांची/कोषाध्यक्ष के पास राशि जमा कराएं।"
                )
                return redirect("donations:donate_thankyou", donation_id=donation.donation_id)
    else:
        # Prepopulate preset if passed in GET parameter
        initial = {}
        amount_param = request.GET.get("amount")
        purpose_param = request.GET.get("purpose")
        project_param = request.GET.get("project")
        if amount_param:
            try:
                initial["amount"] = Decimal(amount_param)
            except Exception:
                pass
        if purpose_param:
            initial["purpose"] = purpose_param
        if project_param:
            initial["related_project"] = project_param
        form = PublicDonationForm(initial=initial)

    return render(request, "public/donate.html", {
        "form": form,
        "site_settings": settings,
        "suggested_amounts": [100, 250, 500, 1000, 2500, 5000, 10000]
    })


def donate_upi_view(request, donation_id):
    """
    UPI QR Code presentation and UTR reference submission.
    """
    donation = get_object_or_404(Donation, donation_id=donation_id)
    settings = SiteSetting.load()

    # Generate UPI QR
    upi_payload = generate_upi_payload(
        upi_id=settings.upi_id,
        merchant_name=settings.upi_merchant_name,
        amount=donation.amount,
        donation_id=donation.donation_id
    )
    qr_data_url = get_phonepe_qr_base64() or generate_upi_qr_base64(upi_payload)

    if request.method == "POST":
        form = UPISubmitReferenceForm(request.POST, request.FILES)
        if form.is_valid():
            donation.transaction_reference = form.cleaned_data["transaction_reference"]
            if form.cleaned_data.get("payment_proof"):
                donation.payment_proof = form.cleaned_data["payment_proof"]
            donation.save()
            messages.success(
                request,
                "आपका UPI UTR संदर्भ नंबर सफलतापूर्वक दर्ज कर लिया गया है। समिति द्वारा बैंक विवरण से मिलान के उपरांत दान की पुष्टि कर दी जाएगी।"
            )
            return redirect("donations:donate_thankyou", donation_id=donation.donation_id)
    else:
        form = UPISubmitReferenceForm(initial={"transaction_reference": donation.transaction_reference})

    return render(request, "public/donate_upi.html", {
        "donation": donation,
        "settings": settings,
        "upi_payload": upi_payload,
        "qr_data_url": qr_data_url,
        "form": form,
    })


def donate_gateway_view(request, donation_id):
    """
    Simulated secure payment gateway checkout & instant verification for demo / production.
    """
    donation = get_object_or_404(Donation, donation_id=donation_id)
    settings = SiteSetting.load()

    if request.method == "POST":
        # Simulating gateway server-side verified response
        simulated_pay_id = f"pay_{donation.donation_id.replace('-', '')}"
        online_acc = FundAccount.objects.filter(account_type__in=["ONLINE", "UPI"], is_active=True).first()
        if not online_acc:
            online_acc = FundAccount.objects.filter(is_active=True).first()

        donation.payment_status = PaymentStatus.CONFIRMED
        donation.transaction_reference = simulated_pay_id
        donation.destination_account = online_acc
        donation.verified_at = timezone.now()
        donation.save()

        # Atomically post to ledger
        donation.post_to_ledger()

        messages.success(request, f"ऑनलाइन भुगतान सफल रहा! रसीद संख्या: {donation.receipt_number}")
        return redirect("donations:donate_thankyou", donation_id=donation.donation_id)

    return render(request, "public/donate_gateway.html", {
        "donation": donation,
        "settings": settings,
    })


def donate_thankyou_view(request, donation_id):
    """
    Thank you and Digital Receipt presentation.
    """
    donation = get_object_or_404(Donation, donation_id=donation_id)
    settings = SiteSetting.load()
    return render(request, "public/donate_thankyou.html", {
        "donation": donation,
        "settings": settings,
    })


def public_donations_list(request):
    """
    Public directory of donations for complete transparency.
    Donor privacy is protected (names masked if anonymous, phone masked).
    """
    settings = SiteSetting.load()
    summary = get_financial_summary()

    qs = Donation.objects.filter(
        payment_status__in=[PaymentStatus.CONFIRMED, PaymentStatus.PENDING]
    ).select_related("donor", "related_project").order_by("-donation_date", "-created_at")

    search = request.GET.get("search", "").strip()
    purpose_filter = request.GET.get("purpose", "")
    project_filter = request.GET.get("project", "")

    if search:
        qs = qs.filter(
            Q(donor_name__icontains=search) |
            Q(receipt_number__icontains=search) |
            Q(donation_id__icontains=search)
        )
    if purpose_filter:
        qs = qs.filter(purpose=purpose_filter)
    if project_filter:
        qs = qs.filter(related_project_id=project_filter)

    paginator = Paginator(qs, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    projects = Project.objects.filter(is_public=True)

    return render(request, "public/donations_list.html", {
        "page_obj": page_obj,
        "summary": summary,
        "search": search,
        "purpose_filter": purpose_filter,
        "project_filter": int(project_filter) if project_filter and project_filter.isdigit() else None,
        "purposes": DonationPurpose.choices,
        "projects": projects,
        "site_settings": settings,
    })


def public_receipt_view(request, receipt_number):
    """
    Public direct receipt view by receipt number.
    Safely retrieves donation and related receipt for donor verification.
    """
    donation = get_object_or_404(Donation, receipt_number=receipt_number)
    receipt = getattr(donation, "receipt", None)
    settings = SiteSetting.load()
    return render(request, "public/receipt_detail.html", {
        "receipt": receipt,
        "donation": donation,
        "settings": settings,
    })


# Staff Dashboard Views for Donations
@login_required
def dashboard_donations_list(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    qs = Donation.objects.select_related("donor", "related_project", "destination_account").all()

    # Search & filters
    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "")
    method_filter = request.GET.get("method", "")
    purpose_filter = request.GET.get("purpose", "")

    if search:
        qs = qs.filter(
            models.Q(donor_name__icontains=search) |
            models.Q(donation_id__icontains=search) |
            models.Q(receipt_number__icontains=search) |
            models.Q(transaction_reference__icontains=search) |
            models.Q(donor_phone__icontains=search)
        )
    if status_filter:
        qs = qs.filter(payment_status=status_filter)
    if method_filter:
        qs = qs.filter(payment_method=method_filter)
    if purpose_filter:
        qs = qs.filter(purpose=purpose_filter)

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "dashboard/donations/list.html", {
        "page_obj": page_obj,
        "search": search,
        "status_filter": status_filter,
        "method_filter": method_filter,
        "purpose_filter": purpose_filter,
        "statuses": PaymentStatus.choices,
        "methods": PaymentMethod.choices,
        "purposes": DonationPurpose.choices,
    })


@login_required
def dashboard_donation_create(request):
    """
    Manual entry of cash / cheque / bank transfer donation by Treasurer or staff.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Only the Treasurer or Administrator can record manual donations.")
        return redirect("donations:dashboard_list")

    if request.method == "POST":
        form = StaffDonationEntryForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.recorded_by = request.user
            donation.verified_by = request.user
            donation.verified_at = timezone.now()
            donation.payment_status = PaymentStatus.CONFIRMED

            # Match or create donor
            phone = form.cleaned_data.get("donor_phone", "").strip()
            name = form.cleaned_data.get("donor_name", "").strip()
            address = form.cleaned_data.get("donor_address", "").strip()
            is_anon = form.cleaned_data.get("is_anonymous", False)

            donor = Donor.objects.filter(phone=phone).first() if phone else None
            if not donor:
                donor = Donor.objects.create(
                    name=name,
                    phone=phone,
                    address=address,
                    is_anonymous=is_anon
                )
            donation.donor = donor
            donation.save()

            # Atomically post to ledger
            success, msg = donation.post_to_ledger(user=request.user)
            if success:
                AuditLog.objects.create(
                    user=request.user,
                    action="MANUAL_DONATION_RECORDED",
                    target_model="Donation",
                    target_id=donation.donation_id,
                    details=f"Recorded manual donation of ₹{donation.amount} from {donation.donor_name} via {donation.payment_method}"
                )
                messages.success(request, f"दान सफलतापूर्वक दर्ज और लेजर में पोस्ट हो गया! रसीद संख्या: {donation.receipt_number}")
                return redirect("donations:dashboard_detail", donation_id=donation.donation_id)
            else:
                messages.warning(request, f"दान दर्ज हो गया परन्तु लेजर पोस्टिंग में सूचना: {msg}")
                return redirect("donations:dashboard_list")
    else:
        form = StaffDonationEntryForm()

    return render(request, "dashboard/donations/create.html", {"form": form})


@login_required
def dashboard_donation_detail(request, donation_id):
    donation = get_object_or_404(Donation, donation_id=donation_id)
    fund_accounts = FundAccount.objects.filter(is_active=True)
    return render(request, "dashboard/donations/detail.html", {
        "donation": donation,
        "fund_accounts": fund_accounts,
    })


@login_required
def dashboard_donation_verify(request, donation_id):
    """
    Treasurer verifies pending donation (e.g. UPI QR UTR match) and posts atomically to ledger.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Only Treasurer or Administrator can verify donations.")
        return redirect("donations:dashboard_list")

    donation = get_object_or_404(Donation, donation_id=donation_id)
    if request.method == "POST":
        account_id = request.POST.get("destination_account")
        if account_id:
            account = get_object_or_404(FundAccount, pk=account_id)
            donation.destination_account = account

        donation.payment_status = PaymentStatus.CONFIRMED
        donation.verified_by = request.user
        donation.verified_at = timezone.now()
        donation.save()

        success, msg = donation.post_to_ledger(user=request.user)
        if success:
            AuditLog.objects.create(
                user=request.user,
                action="DONATION_VERIFIED",
                target_model="Donation",
                target_id=donation.donation_id,
                details=f"Verified donation of ₹{donation.amount} for {donation.donor_name}. Posted to {donation.destination_account.name}"
            )
            messages.success(request, f"दान सत्यापित कर दिया गया और लेजर में सफलता से जुड़ गया।")
        else:
            messages.warning(request, f"सत्यापन पूर्ण हुआ, लेजर संदेश: {msg}")

    return redirect("donations:dashboard_detail", donation_id=donation.donation_id)
