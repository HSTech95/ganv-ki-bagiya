from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Project, ProjectUpdate, ProjectType, ProjectStatus
from .forms import ProjectForm, ProjectUpdateForm
from apps.donations.models import Donation, PaymentStatus
from apps.expenses.models import Expense, ExpensePaymentStatus
from apps.accounts.models import AuditLog


def projects_list(request):
    """
    Public listing of Garden and Kabristan development projects.
    """
    type_filter = request.GET.get("type", "")
    status_filter = request.GET.get("status", "")

    qs = Project.objects.filter(is_public=True)
    if type_filter:
        qs = qs.filter(project_type=type_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)

    return render(request, "public/projects_list.html", {
        "projects": qs,
        "type_filter": type_filter,
        "status_filter": status_filter,
        "project_types": ProjectType.choices,
        "project_statuses": ProjectStatus.choices,
    })


def project_detail(request, slug):
    """
    Public detailed view of a specific project with progress timeline and public budget summary.
    """
    project = get_object_or_404(Project, slug=slug, is_public=True)
    updates = project.updates.all()
    project_donations = project.donations.filter(payment_status=PaymentStatus.CONFIRMED).order_by("-donation_date")[:10]
    project_expenses = project.expenses.filter(payment_status=ExpensePaymentStatus.PAID).order_by("-paid_date")[:10]

    return render(request, "public/project_detail.html", {
        "project": project,
        "updates": updates,
        "project_donations": project_donations,
        "project_expenses": project_expenses,
    })


# Staff Dashboard Views for Projects
@login_required
def dashboard_projects_list(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "TREASURER", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    projects = Project.objects.all()
    return render(request, "dashboard/projects/list.html", {"projects": projects})


@login_required
def dashboard_project_create(request):
    if not (request.user.is_super_admin or request.user.role in ["PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Only Project Managers or Committee President can create projects.")
        return redirect("projects:dashboard_list")

    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            proj = form.save(commit=False)
            if not proj.manager:
                proj.manager = request.user
            proj.save()

            AuditLog.objects.create(
                user=request.user,
                action="PROJECT_CREATED",
                target_model="Project",
                target_id=str(proj.id),
                details=f"Created project {proj.name} with budget ₹{proj.estimated_budget}"
            )
            messages.success(request, f"नया प्रोजेक्ट '{proj.name}' सफलतापूर्वक बनाया गया।")
            return redirect("projects:dashboard_detail", pk=proj.pk)
    else:
        form = ProjectForm(initial={"start_date": timezone.now().date()})

    return render(request, "dashboard/projects/create.html", {"form": form})


@login_required
def dashboard_project_detail(request, pk):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "TREASURER", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST" and "post_update" in request.POST:
        update_form = ProjectUpdateForm(request.POST, request.FILES)
        if update_form.is_valid():
            up = update_form.save(commit=False)
            up.project = project
            up.posted_by = request.user
            up.save()

            # Optionally update progress percent
            new_pct = request.POST.get("progress_percentage")
            if new_pct:
                try:
                    project.progress_percentage = int(new_pct)
                    project.save(update_fields=["progress_percentage"])
                except Exception:
                    pass

            messages.success(request, "प्रोजेक्ट प्रगति अपडेट सफलतापूर्वक पोस्ट किया गया।")
            return redirect("projects:dashboard_detail", pk=project.pk)
    else:
        update_form = ProjectUpdateForm(initial={"update_date": timezone.now().date()})

    updates = project.updates.all()
    expenses = project.expenses.all()
    donations = project.donations.all()

    return render(request, "dashboard/projects/detail.html", {
        "project": project,
        "update_form": update_form,
        "updates": updates,
        "expenses": expenses,
        "donations": donations,
    })


@login_required
def dashboard_project_edit(request, pk):
    if not (request.user.is_super_admin or request.user.role in ["PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("projects:dashboard_list")

    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "प्रोजेक्ट का विवरण सफलतापूर्वक अपडेट किया गया।")
            return redirect("projects:dashboard_detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, "dashboard/projects/edit.html", {"form": form, "project": project})
