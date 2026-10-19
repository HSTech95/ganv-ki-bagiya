import json
from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models

from apps.finance.services import get_financial_summary
from apps.donations.models import Donation, PaymentStatus
from apps.expenses.models import Expense, ExpenseApprovalStatus, ExpensePaymentStatus, ExpenseCategory
from apps.projects.models import Project, ProjectStatus
from apps.maintenance.models import MaintenanceTask, TaskStatus
from apps.accounts.models import CustomUser


@login_required
def dashboard_home(request):
    """
    Main Committee & Staff Management Dashboard.
    """
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT", "PROJECT_MANAGER", "VOLUNTEER"]):
        messages.info(request, "Welcome to Ganv Ki Bagiya! Public portal access.")
        return redirect("public:home")

    summary = get_financial_summary()
    active_projects_count = Project.objects.filter(status=ProjectStatus.ACTIVE).count()

    # Recent Records
    latest_donations = Donation.objects.select_related("donor", "related_project").order_by("-created_at")[:6]
    latest_expenses = Expense.objects.select_related("created_by", "related_project").order_by("-created_at")[:6]
    pending_approvals = Expense.objects.filter(approval_status=ExpenseApprovalStatus.SUBMITTED).select_related("created_by")[:5]
    upcoming_tasks = MaintenanceTask.objects.filter(status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]).order_by("scheduled_date")[:5]

    # Chart 1: Monthly income vs expense (last 6 months)
    today = timezone.now().date()
    monthly_labels = []
    monthly_income = []
    monthly_expense = []

    for i in range(5, -1, -1):
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

    # Chart 2: Expense category breakdown
    category_totals = Expense.objects.filter(payment_status=ExpensePaymentStatus.PAID).values("category").annotate(total=models.Sum("amount")).order_by("-total")
    cat_labels = []
    cat_data = []
    cat_dict = dict(ExpenseCategory.choices)
    for c in category_totals:
        cat_labels.append(str(cat_dict.get(c["category"], c["category"])))
        cat_data.append(float(c["total"]))

    # Chart 3: Project spending
    projects = Project.objects.filter(is_public=True)[:6]
    proj_labels = [p.name[:20] for p in projects]
    proj_spent = [float(p.actual_expenditure) for p in projects]
    proj_budgets = [float(p.estimated_budget) for p in projects]

    # Chart 4: Daily donation collection (last 14 days)
    daily_labels = []
    daily_donations = []
    for i in range(13, -1, -1):
        d_day = today - timedelta(days=i)
        d_label = d_day.strftime("%d %b")
        d_sum = Donation.objects.filter(
            payment_status=PaymentStatus.CONFIRMED,
            donation_date=d_day
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
        daily_labels.append(d_label)
        daily_donations.append(float(d_sum))

    charts_payload = {
        "monthly_labels": json.dumps(monthly_labels),
        "monthly_income": json.dumps(monthly_income),
        "monthly_expense": json.dumps(monthly_expense),
        "category_labels": json.dumps(cat_labels),
        "category_data": json.dumps(cat_data),
        "proj_labels": json.dumps(proj_labels),
        "proj_spent": json.dumps(proj_spent),
        "proj_budgets": json.dumps(proj_budgets),
        "daily_labels": json.dumps(daily_labels),
        "daily_donations": json.dumps(daily_donations),
    }

    context = {
        "summary": summary,
        "active_projects_count": active_projects_count,
        "latest_donations": latest_donations,
        "latest_expenses": latest_expenses,
        "pending_approvals": pending_approvals,
        "upcoming_tasks": upcoming_tasks,
        "charts": charts_payload,
    }

    return render(request, "dashboard/index.html", context)
