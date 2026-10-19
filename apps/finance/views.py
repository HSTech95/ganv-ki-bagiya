import json
from decimal import Decimal
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone

from .models import (
    FundAccount, LedgerEntry, LedgerEntryType,
    DailyBalanceSnapshot, AccountTransfer, BankReconciliation
)
from .forms import AccountTransferForm, BankReconciliationForm, FundAccountForm, ReversalForm
from .services import (
    get_financial_summary, calculate_daily_balance,
    execute_account_transfer, reverse_ledger_entry
)
from apps.donations.models import Donation, PaymentStatus, DonationPurpose
from apps.expenses.models import Expense, ExpensePaymentStatus, ExpenseCategory
from apps.projects.models import Project


def transparency_view(request):
    """
    Public financial transparency portal.
    Strict privacy compliance: Personal phones are masked, donor anonymity respected.
    """
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    project_id = request.GET.get("project")
    category_filter = request.GET.get("category")
    year_filter = request.GET.get("year")

    # Dates
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except Exception:
            pass
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
        except Exception:
            pass

    if year_filter:
        try:
            y = int(year_filter)
            start_date = date(y, 4, 1)  # Indian Financial Year: April 1 to March 31
            end_date = date(y + 1, 3, 31)
        except Exception:
            pass

    financial_summary = get_financial_summary(start_date=start_date, end_date=end_date, project_id=project_id)

    # Project-wise financial breakdowns
    projects_breakdown = []
    for proj in Project.objects.filter(is_public=True):
        actual_spent = proj.actual_expenditure
        funds_in = proj.total_funds_received
        budget = proj.estimated_budget
        projects_breakdown.append({
            "project": proj,
            "budget": budget,
            "spent": actual_spent,
            "received": funds_in,
            "remaining": max(0, float(budget) - float(actual_spent)),
            "progress_percent": proj.progress_percentage
        })

    # Recent public transactions (Confirmed & Verifying Donations & Paid Expenses)
    recent_donations = Donation.objects.filter(
        payment_status__in=[PaymentStatus.CONFIRMED, PaymentStatus.PENDING]
    ).select_related("donor", "related_project").order_by("-donation_date", "-created_at")[:15]
    recent_expenses = Expense.objects.filter(payment_status=ExpensePaymentStatus.PAID).select_related("related_project").order_by("-expense_date")[:15]

    # Category breakdown for Chart.js
    category_totals = Expense.objects.filter(payment_status=ExpensePaymentStatus.PAID).values("category").annotate(total=models.Sum("amount")).order_by("-total")
    cat_labels = []
    cat_data = []
    cat_dict = dict(ExpenseCategory.choices)
    for c in category_totals:
        cat_labels.append(str(cat_dict.get(c["category"], c["category"])))
        cat_data.append(float(c["total"]))

    # Monthly income vs expense data for Chart.js (last 6 months)
    today = timezone.now().date()
    monthly_labels = []
    monthly_income = []
    monthly_expense = []

    for i in range(5, -1, -1):
        # Calculate month start and end
        m_year = today.year
        m_month = today.month - i
        while m_month <= 0:
            m_month += 12
            m_year -= 1

        m_start = date(m_year, m_month, 1)
        if m_month == 12:
            m_end = date(m_year + 1, 1, 1) - timedelta(days=1)
        else:
            m_end = date(m_year, m_month + 1, 1) - timedelta(days=1)

        month_label = m_start.strftime("%b %Y")
        inc = Donation.objects.filter(
            payment_status=PaymentStatus.CONFIRMED,
            donation_date__gte=m_start,
            donation_date__lte=m_end
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

        exp = Expense.objects.filter(
            payment_status=ExpensePaymentStatus.PAID,
            paid_date__gte=m_start,
            paid_date__lte=m_end
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

        monthly_labels.append(month_label)
        monthly_income.append(float(inc))
        monthly_expense.append(float(exp))

    chart_data = {
        "monthly_labels": json.dumps(monthly_labels),
        "monthly_income": json.dumps(monthly_income),
        "monthly_expense": json.dumps(monthly_expense),
        "category_labels": json.dumps(cat_labels),
        "category_data": json.dumps(cat_data),
    }

    # Available projects for filter dropdown
    all_projects = Project.objects.filter(is_public=True)

    return render(request, "public/transparency.html", {
        "summary": financial_summary,
        "projects_breakdown": projects_breakdown,
        "recent_donations": recent_donations,
        "recent_expenses": recent_expenses,
        "chart_data": chart_data,
        "all_projects": all_projects,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "selected_project": int(project_id) if project_id else None,
        "selected_year": year_filter,
    })


# Dashboard Finance Views
@login_required
def dashboard_ledger_view(request):
    """
    Immutable General Ledger view.
    """
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT"]):
        messages.error(request, "Access restricted to financial personnel.")
        return redirect("public:home")

    qs = LedgerEntry.objects.select_related("account", "posted_by", "reference_donation", "reference_expense").all()

    # Search & filters
    search = request.GET.get("search", "").strip()
    account_filter = request.GET.get("account")
    type_filter = request.GET.get("type")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if search:
        qs = qs.filter(
            models.Q(entry_id__icontains=search) |
            models.Q(description__icontains=search)
        )
    if account_filter:
        qs = qs.filter(account_id=account_filter)
    if type_filter:
        qs = qs.filter(entry_type=type_filter)
    if start_date:
        qs = qs.filter(entry_date__gte=start_date)
    if end_date:
        qs = qs.filter(entry_date__lte=end_date)

    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    accounts = FundAccount.objects.filter(is_active=True)
    reversal_form = ReversalForm()

    return render(request, "dashboard/finance/ledger.html", {
        "page_obj": page_obj,
        "accounts": accounts,
        "entry_types": LedgerEntryType.choices,
        "search": search,
        "account_filter": int(account_filter) if account_filter else None,
        "type_filter": type_filter,
        "start_date": start_date,
        "end_date": end_date,
        "reversal_form": reversal_form,
    })


@login_required
def dashboard_daily_balances_view(request):
    """
    Daily Opening & Closing Balance Ledger.
    """
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    # If action is requested to recalculate today or a specific date
    if request.method == "POST" and "recalculate_date" in request.POST:
        target_str = request.POST.get("recalculate_date")
        try:
            target_d = date.fromisoformat(target_str)
            calculate_daily_balance(target_d)
            messages.success(request, f"दिन {target_d} का प्रारंभिक व अंतिम बैलेंस सफलतापूर्वक पुनर्गणित किया गया।")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect("finance:dashboard_daily_balances")

    snapshots = DailyBalanceSnapshot.objects.all()
    paginator = Paginator(snapshots, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "dashboard/finance/daily_balances.html", {
        "page_obj": page_obj,
        "today": timezone.now().date(),
    })


@login_required
def dashboard_accounts_view(request):
    """
    List and create fund accounts (Cash in hand, Bank accounts, Online gateway pools).
    """
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    accounts = FundAccount.objects.all()

    if request.method == "POST":
        if not request.user.is_super_admin:
            messages.error(request, "Only Super Admin can create or modify accounts.")
            return redirect("finance:dashboard_accounts")
        form = FundAccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "नया खाता सफलतापूर्वक जोड़ा गया।")
            return redirect("finance:dashboard_accounts")
    else:
        form = FundAccountForm()

    return render(request, "dashboard/finance/accounts.html", {
        "accounts": accounts,
        "form": form,
    })


@login_required
def dashboard_transfer_view(request):
    """
    Execute atomic internal transfer between accounts.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Only Treasurer or Administrator can transfer funds.")
        return redirect("finance:dashboard_accounts")

    if request.method == "POST":
        form = AccountTransferForm(request.POST)
        if form.is_valid():
            from_acc = form.cleaned_data["from_account"]
            to_acc = form.cleaned_data["to_account"]
            amt = form.cleaned_data["amount"]
            reason = form.cleaned_data["reason"]
            t_date = form.cleaned_data["transfer_date"]

            success, msg = execute_account_transfer(
                from_account=from_acc,
                to_account=to_acc,
                amount=amt,
                reason=reason,
                user=request.user,
                transfer_date=t_date
            )
            if success:
                messages.success(request, msg)
                return redirect("finance:dashboard_ledger")
            else:
                messages.error(request, msg)
    else:
        form = AccountTransferForm(initial={"transfer_date": timezone.now().date()})

    transfers = AccountTransfer.objects.select_related("from_account", "to_account", "initiated_by").all()[:15]
    return render(request, "dashboard/finance/transfer.html", {
        "form": form,
        "transfers": transfers,
    })


@login_required
def dashboard_reconciliation_view(request):
    """
    Bank reconciliation view.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Access restricted.")
        return redirect("finance:dashboard_ledger")

    if request.method == "POST":
        form = BankReconciliationForm(request.POST)
        if form.is_valid():
            recon = form.save(commit=False)
            recon.verified_by = request.user
            recon.book_balance = recon.account.current_balance
            recon.discrepancy = recon.statement_balance - recon.book_balance
            recon.is_balanced = (recon.discrepancy == Decimal("0.00"))
            recon.save()

            if recon.is_balanced:
                messages.success(request, f"{recon.account.name} का बैंक समाधान पूर्ण हुआ। शेष राशि शत-प्रतिशत मेल खाती है!")
            else:
                messages.warning(request, f"{recon.account.name} में ₹{recon.discrepancy} का अंतर चिन्हित किया गया है। कृपया विवरण की समीक्षा करें।")
            return redirect("finance:dashboard_reconciliation")
    else:
        form = BankReconciliationForm(initial={"statement_date": timezone.now().date()})

    reconciliations = BankReconciliation.objects.select_related("account", "verified_by").all()
    return render(request, "dashboard/finance/reconciliation.html", {
        "form": form,
        "reconciliations": reconciliations,
    })


@login_required
def dashboard_reverse_entry_view(request):
    """
    POST view to atomically reverse a posted ledger entry.
    """
    if not request.user.is_super_admin and request.user.role != "TREASURER":
        messages.error(request, "Only Treasurer or Super Admin can issue ledger reversals.")
        return redirect("finance:dashboard_ledger")

    if request.method == "POST":
        form = ReversalForm(request.POST)
        if form.is_valid():
            entry_id = form.cleaned_data["entry_id"]
            reason = form.cleaned_data["reason"]
            success, msg = reverse_ledger_entry(entry_id=entry_id, user=request.user, reason=reason)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)

    return redirect("finance:dashboard_ledger")
