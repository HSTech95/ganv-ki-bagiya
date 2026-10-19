from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import models

from .models import (
    Expense, ExpenseAttachment, ExpenseApprovalLog,
    ExpenseApprovalStatus, ExpensePaymentStatus, ExpenseCategory
)
from .forms import ExpenseCreateForm, ExpenseApprovalForm, ExpensePaymentForm
from apps.finance.models import FundAccount
from apps.accounts.models import AuditLog


@login_required
def dashboard_expenses_list(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    qs = Expense.objects.select_related("created_by", "approved_by", "related_project", "paid_from_account").all()

    search = request.GET.get("search", "").strip()
    approval_filter = request.GET.get("approval", "")
    payment_filter = request.GET.get("payment", "")
    category_filter = request.GET.get("category", "")

    if search:
        qs = qs.filter(
            models.Q(description__icontains=search) |
            models.Q(expense_id__icontains=search) |
            models.Q(vendor_name__icontains=search) |
            models.Q(bill_number__icontains=search)
        )
    if approval_filter:
        qs = qs.filter(approval_status=approval_filter)
    if payment_filter:
        qs = qs.filter(payment_status=payment_filter)
    if category_filter:
        qs = qs.filter(category=category_filter)

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "dashboard/expenses/list.html", {
        "page_obj": page_obj,
        "search": search,
        "approval_filter": approval_filter,
        "payment_filter": payment_filter,
        "category_filter": category_filter,
        "approval_statuses": ExpenseApprovalStatus.choices,
        "payment_statuses": ExpensePaymentStatus.choices,
        "categories": ExpenseCategory.choices,
    })


@login_required
def dashboard_expense_create(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Only committee members can record expenses.")
        return redirect("expenses:dashboard_list")

    if request.method == "POST":
        form = ExpenseCreateForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            action_type = request.POST.get("action", "SUBMIT")
            if action_type == "SUBMIT":
                expense.approval_status = ExpenseApprovalStatus.SUBMITTED
            else:
                expense.approval_status = ExpenseApprovalStatus.DRAFT
            expense.save()

            # Handle extra files if uploaded
            extra_files = request.FILES.getlist("extra_files")
            for f in extra_files:
                ExpenseAttachment.objects.create(expense=expense, file=f, title=f.name)

            ExpenseApprovalLog.objects.create(
                expense=expense,
                action="SUBMITTED" if action_type == "SUBMIT" else "DRAFT_SAVED",
                user=request.user,
                comments="Expense entry created."
            )

            AuditLog.objects.create(
                user=request.user,
                action="EXPENSE_CREATED",
                target_model="Expense",
                target_id=expense.expense_id,
                details=f"Created expense {expense.expense_id} for ₹{expense.amount} ({expense.description})"
            )

            messages.success(request, f"खर्च प्रविष्टि ({expense.expense_id}) सफलतापूर्वक दर्ज हो गई।")
            return redirect("expenses:dashboard_detail", expense_id=expense.expense_id)
    else:
        form = ExpenseCreateForm(initial={"expense_date": timezone.now().date()})

    return render(request, "dashboard/expenses/create.html", {"form": form})


@login_required
def dashboard_expense_detail(request, expense_id):
    expense = get_object_or_404(Expense, expense_id=expense_id)
    approval_form = ExpenseApprovalForm()
    payment_form = ExpensePaymentForm(initial={"paid_date": timezone.now().date()})

    # Self-approval check flag
    can_user_approve = request.user.can_approve_expenses and (request.user.is_superuser or expense.created_by != request.user)

    return render(request, "dashboard/expenses/detail.html", {
        "expense": expense,
        "approval_form": approval_form,
        "payment_form": payment_form,
        "can_user_approve": can_user_approve,
    })


@login_required
def dashboard_expense_approve(request, expense_id):
    """
    Committee President or Super Admin review & approval.
    Enforces rule: users cannot approve their own expenses.
    """
    if not request.user.can_approve_expenses:
        messages.error(request, "Only the Committee President or Super Admin can approve expenses.")
        return redirect("expenses:dashboard_detail", expense_id=expense_id)

    expense = get_object_or_404(Expense, expense_id=expense_id)

    if expense.created_by == request.user and not request.user.is_superuser:
        messages.error(request, "स्वयं द्वारा दर्ज किए गए खर्च को आप स्वयं स्वीकृत नहीं कर सकते। अन्य समिति पदाधिकारी की स्वीकृति आवश्यक है।")
        return redirect("expenses:dashboard_detail", expense_id=expense_id)

    if request.method == "POST":
        form = ExpenseApprovalForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data["decision"]
            comments = form.cleaned_data.get("comments", "")

            expense.approval_status = decision
            expense.approved_by = request.user
            expense.approval_date = timezone.now()
            expense.approval_notes = comments
            expense.save()

            ExpenseApprovalLog.objects.create(
                expense=expense,
                action=decision,
                user=request.user,
                comments=comments
            )

            AuditLog.objects.create(
                user=request.user,
                action=f"EXPENSE_{decision}",
                target_model="Expense",
                target_id=expense.expense_id,
                details=f"Expense {expense.expense_id} was {decision.lower()} by {request.user.username}. Notes: {comments}"
            )

            if decision == "APPROVED":
                messages.success(request, f"खर्च स्वीकृत हो गया है। अब कोषाध्यक्ष द्वारा इसका भुगतान दर्ज किया जा सकता है।")
            else:
                messages.warning(request, f"खर्च अस्वीकृत कर दिया गया है।")

    return redirect("expenses:dashboard_detail", expense_id=expense_id)


@login_required
def dashboard_expense_pay(request, expense_id):
    """
    Treasurer records the actual payment and atomically updates the fund account and ledger.
    """
    if not request.user.can_manage_finances:
        messages.error(request, "Only the Treasurer or Administrator can record payments.")
        return redirect("expenses:dashboard_detail", expense_id=expense_id)

    expense = get_object_or_404(Expense, expense_id=expense_id)

    if expense.approval_status != ExpenseApprovalStatus.APPROVED:
        messages.error(request, "Cannot disburse payment for unapproved expense.")
        return redirect("expenses:dashboard_detail", expense_id=expense_id)

    if expense.payment_status == ExpensePaymentStatus.PAID:
        messages.info(request, "This expense is already marked as paid.")
        return redirect("expenses:dashboard_detail", expense_id=expense_id)

    if request.method == "POST":
        form = ExpensePaymentForm(request.POST)
        if form.is_valid():
            account = form.cleaned_data["paid_from_account"]
            method = form.cleaned_data["payment_method"]
            ref = form.cleaned_data["payment_reference"]
            paid_date = form.cleaned_data["paid_date"]

            success, msg = expense.record_payment(
                account=account,
                method=method,
                reference=ref,
                user=request.user,
                paid_date=paid_date
            )

            if success:
                AuditLog.objects.create(
                    user=request.user,
                    action="EXPENSE_PAID",
                    target_model="Expense",
                    target_id=expense.expense_id,
                    details=f"Paid ₹{expense.amount} for {expense.expense_id} from {account.name} ({method}, Ref: {ref})"
                )
                messages.success(request, "भुगतान सफलतापूर्वक दर्ज कर दिया गया और वित्तीय लेजर अपडेट हो गया!")
            else:
                messages.error(request, f"भुगतान दर्ज करने में त्रुटि: {msg}")

    return redirect("expenses:dashboard_detail", expense_id=expense_id)
