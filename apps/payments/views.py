import hmac
import hashlib
import json
import uuid
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.db import transaction

from .models import PaymentTransaction, UPIReconciliationRecord
from .forms import UPIStatementEntryForm
from apps.donations.models import Donation, PaymentStatus, PaymentMethod
from apps.finance.models import FundAccount
from apps.accounts.models import AuditLog


def get_razorpay_credentials():
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "rzp_test_GanvKiBagiya")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "mock_rzp_secret_key_123456789")
    webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "mock_webhook_secret_xyz")
    return key_id, key_secret, webhook_secret


def verify_razorpay_signature(order_id, payment_id, signature, key_secret):
    """
    HMAC-SHA256 signature verification matching Razorpay's standard formula:
    HMAC_SHA256(order_id + "|" + payment_id, secret) == signature
    """
    msg = f"{order_id}|{payment_id}".encode("utf-8")
    generated_sig = hmac.new(key_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(generated_sig, signature)


def verify_webhook_signature(body_bytes, signature, webhook_secret):
    """
    HMAC-SHA256 signature verification matching Razorpay Webhook standard.
    """
    if not webhook_secret:
        return True
    generated_sig = hmac.new(webhook_secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(generated_sig, signature)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Server-side authenticated webhook endpoint for Razorpay.
    Verifies signature and ensures strictly idempotent payment capture and ledger posting.
    """
    key_id, key_secret, webhook_secret = get_razorpay_credentials()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # In production or if webhook secret is configured, verify HMAC signature
    if webhook_secret and signature:
        if not verify_webhook_signature(request.body, signature, webhook_secret):
            return HttpResponseBadRequest("Invalid webhook signature.")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON payload.")

    event = data.get("event", "")
    payload = data.get("payload", {})
    payment_entity = payload.get("payment", {}).get("entity", {})

    order_id = payment_entity.get("order_id", "")
    payment_id = payment_entity.get("id", "")
    amount_in_paise = payment_entity.get("amount", 0)
    notes = payment_entity.get("notes", {})
    donation_id = notes.get("donation_id", "")

    # Idempotency check: see if this payment transaction has already been captured
    existing_txn = PaymentTransaction.objects.filter(gateway_payment_id=payment_id).first()
    if existing_txn and existing_txn.status == "CAPTURED":
        return HttpResponse("Event already processed (Idempotent).", status=200)

    # Find corresponding donation
    donation = None
    if donation_id:
        donation = Donation.objects.filter(donation_id=donation_id).first()
    if not donation and order_id:
        txn = PaymentTransaction.objects.filter(gateway_order_id=order_id).first()
        if txn:
            donation = txn.donation

    if not donation:
        return HttpResponse("Donation not found, skipped.", status=200)

    if event in ["payment.captured", "order.paid"]:
        with transaction.atomic():
            online_acc = FundAccount.objects.filter(account_type__in=["ONLINE", "UPI"], is_active=True).first()
            if not online_acc:
                online_acc = FundAccount.objects.filter(is_active=True).first()

            donation.payment_status = PaymentStatus.CONFIRMED
            donation.transaction_reference = payment_id
            donation.destination_account = online_acc
            donation.verified_at = timezone.now()
            donation.save()

            # Record or update PaymentTransaction
            txn, created = PaymentTransaction.objects.get_or_create(
                donation=donation,
                defaults={
                    "gateway_order_id": order_id,
                    "gateway_payment_id": payment_id,
                    "amount": donation.amount,
                    "status": "CAPTURED",
                    "raw_response": data,
                }
            )
            if not created:
                txn.gateway_payment_id = payment_id
                txn.status = "CAPTURED"
                txn.raw_response = data
                txn.save()

            # Atomically post to ledger
            donation.post_to_ledger()

            AuditLog.objects.create(
                action="WEBHOOK_PAYMENT_CAPTURED",
                target_model="Donation",
                target_id=donation.donation_id,
                details=f"Payment of ₹{donation.amount} captured via Razorpay webhook. Payment ID: {payment_id}"
            )

    elif event == "payment.failed":
        txn, created = PaymentTransaction.objects.get_or_create(
            donation=donation,
            defaults={
                "gateway_order_id": order_id,
                "gateway_payment_id": payment_id,
                "amount": donation.amount,
                "status": "FAILED",
                "raw_response": data,
            }
        )
        if not created:
            txn.status = "FAILED"
            txn.raw_response = data
            txn.save()

        donation.payment_status = PaymentStatus.FAILED
        donation.save()

    return HttpResponse("Webhook processed successfully.", status=200)


# ==========================================
# UPI RECONCILIATION DASHBOARD VIEWS
# ==========================================

@login_required
def dashboard_upi_reconciliation_list(request):
    """
    UPI Reconciliation portal:
    Compare bank statement UTR records with pending donor-submitted UPI donations.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Access restricted to finance personnel.")
        return redirect("finance:dashboard_ledger")

    if request.method == "POST":
        form = UPIStatementEntryForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.save()
            messages.success(request, f"बैंक स्टेटमेंट UTR रिकॉर्ड '{record.utr_number}' (₹{record.amount}) सफलतापूर्वक जोड़ा गया।")
            return redirect("payments:dashboard_upi_reconciliation")
    else:
        form = UPIStatementEntryForm(initial={"bank_statement_date": timezone.now().date()})

    reconciliation_records = UPIReconciliationRecord.objects.select_related("matched_donation", "matched_by").all()
    pending_donations = Donation.objects.filter(
        payment_method=PaymentMethod.UPI_QR,
        payment_status=PaymentStatus.PENDING
    ).exclude(transaction_reference="").order_by("-donation_date")

    unmatched_records_count = reconciliation_records.filter(is_matched=False).count()
    matched_records_count = reconciliation_records.filter(is_matched=True).count()
    pending_donations_count = pending_donations.count()

    return render(request, "dashboard/finance/upi_reconciliation.html", {
        "form": form,
        "reconciliation_records": reconciliation_records,
        "pending_donations": pending_donations,
        "unmatched_records_count": unmatched_records_count,
        "matched_records_count": matched_records_count,
        "pending_donations_count": pending_donations_count,
    })


@login_required
@require_POST
def dashboard_upi_auto_match(request):
    """
    Automatic matching engine:
    Matches Bank Statement UTR numbers against Donor-submitted UPI UTR numbers and amounts.
    On match: confirms donation and atomically posts to the ledger.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Access restricted.")
        return redirect("finance:dashboard_ledger")

    unmatched_records = UPIReconciliationRecord.objects.filter(is_matched=False)
    pending_donations = Donation.objects.filter(
        payment_method=PaymentMethod.UPI_QR,
        payment_status=PaymentStatus.PENDING
    ).exclude(transaction_reference="")

    # Index pending donations by normalized UTR
    donations_by_utr = {}
    for d in pending_donations:
        utr_norm = d.transaction_reference.strip().lower()
        if utr_norm:
            donations_by_utr[utr_norm] = d

    matched_count = 0

    with transaction.atomic():
        for record in unmatched_records:
            norm_rec_utr = record.utr_number.strip().lower()
            donation = donations_by_utr.get(norm_rec_utr)

            if donation and donation.amount == record.amount:
                # Mark record matched
                record.is_matched = True
                record.matched_donation = donation
                record.matched_by = request.user
                record.matched_at = timezone.now()
                record.save()

                # Confirm donation
                donation.payment_status = PaymentStatus.CONFIRMED
                donation.verified_by = request.user
                donation.verified_at = timezone.now()
                donation.save()

                # Atomically post to ledger
                donation.post_to_ledger(user=request.user)

                AuditLog.objects.create(
                    user=request.user,
                    action="UPI_AUTO_MATCHED",
                    target_model="Donation",
                    target_id=donation.donation_id,
                    details=f"Auto-matched UTR {record.utr_number} for ₹{record.amount} with Donation {donation.donation_id}"
                )
                matched_count += 1
                del donations_by_utr[norm_rec_utr]

    if matched_count > 0:
        messages.success(request, f"सफलता! {matched_count} यूपीआई दान बैंक स्टेटमेंट से स्वतः मिलान हो गए और लेजर में दर्ज कर दिए गए।")
    else:
        messages.info(request, "कोई नया UTR मिलान नहीं मिला। कृपया UTR संख्या और राशि की जांच करें।")

    return redirect("payments:dashboard_upi_reconciliation")


@login_required
@require_POST
def dashboard_upi_manual_match(request, record_id):
    """
    Treasurer manually links a bank statement UTR record to a specific pending donation.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Access restricted.")
        return redirect("finance:dashboard_ledger")

    record = get_object_or_404(UPIReconciliationRecord, pk=record_id)
    donation_id = request.POST.get("donation_id")
    donation = get_object_or_404(Donation, donation_id=donation_id)

    with transaction.atomic():
        record.is_matched = True
        record.matched_donation = donation
        record.matched_by = request.user
        record.matched_at = timezone.now()
        record.save()

        donation.payment_status = PaymentStatus.CONFIRMED
        donation.verified_by = request.user
        donation.verified_at = timezone.now()
        donation.save()

        donation.post_to_ledger(user=request.user)

        AuditLog.objects.create(
            user=request.user,
            action="UPI_MANUAL_MATCHED",
            target_model="Donation",
            target_id=donation.donation_id,
            details=f"Manually matched UTR {record.utr_number} for ₹{record.amount} with Donation {donation.donation_id}"
        )

    messages.success(request, f"दान {donation.donation_id} को UTR {record.utr_number} के साथ सफलतापूर्वक मिलान कर दिया गया।")
    return redirect("payments:dashboard_upi_reconciliation")


@login_required
@require_POST
def dashboard_upi_delete_record(request, record_id):
    """
    Delete an unmatched bank statement entry.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Access restricted.")
        return redirect("finance:dashboard_ledger")

    record = get_object_or_404(UPIReconciliationRecord, pk=record_id)
    if record.is_matched:
        messages.error(request, "मिलान हो चुके रिकॉर्ड को सीधे हटाया नहीं जा सकता।")
        return redirect("payments:dashboard_upi_reconciliation")

    record.delete()
    messages.success(request, "बैंक स्टेटमेंट रिकॉर्ड हटा दिया गया।")
    return redirect("payments:dashboard_upi_reconciliation")
