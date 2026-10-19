from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import MaintenanceTask, FacilityType, TaskStatus, TaskPriority, TaskType
from .forms import MaintenanceTaskForm, TaskCompleteForm
from apps.accounts.models import AuditLog


@login_required
def dashboard_maintenance_list(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "TREASURER", "PROJECT_MANAGER", "VOLUNTEER"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    facility_filter = request.GET.get("facility", "")
    status_filter = request.GET.get("status", "")
    priority_filter = request.GET.get("priority", "")

    qs = MaintenanceTask.objects.select_related("assigned_volunteer", "project", "created_by").all()
    if facility_filter:
        qs = qs.filter(facility=facility_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if priority_filter:
        qs = qs.filter(priority=priority_filter)

    return render(request, "dashboard/maintenance/list.html", {
        "tasks": qs,
        "facility_filter": facility_filter,
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "facilities": FacilityType.choices,
        "statuses": TaskStatus.choices,
        "priorities": TaskPriority.choices,
    })


@login_required
def dashboard_maintenance_create(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Unauthorized to schedule maintenance tasks.")
        return redirect("maintenance:dashboard_list")

    if request.method == "POST":
        form = MaintenanceTaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()

            AuditLog.objects.create(
                user=request.user,
                action="MAINTENANCE_SCHEDULED",
                target_model="MaintenanceTask",
                target_id=str(task.id),
                details=f"Scheduled maintenance: {task.title} ({task.facility})"
            )
            messages.success(request, f"रख-रखाव कार्य '{task.title}' सफलतापूर्वक शेड्यूल कर दिया गया।")
            return redirect("maintenance:dashboard_list")
    else:
        form = MaintenanceTaskForm(initial={"scheduled_date": timezone.now().date()})

    return render(request, "dashboard/maintenance/create.html", {"form": form})


@login_required
def dashboard_maintenance_detail(request, pk):
    task = get_object_or_404(MaintenanceTask, pk=pk)

    if request.method == "POST" and "complete_task" in request.POST:
        form = TaskCompleteForm(request.POST, request.FILES)
        if form.is_valid():
            task.completed_date = form.cleaned_data["completion_date"]
            task.completion_notes = form.cleaned_data["completion_notes"]
            if form.cleaned_data.get("after_photo"):
                task.after_photo = form.cleaned_data["after_photo"]
            task.status = TaskStatus.COMPLETED
            task.save()
            messages.success(request, f"कार्य '{task.title}' सफलतापूर्वक पूर्ण चिन्हित कर दिया गया!")
            return redirect("maintenance:dashboard_detail", pk=task.pk)
    else:
        form = TaskCompleteForm(initial={"completion_date": timezone.now().date()})

    return render(request, "dashboard/maintenance/detail.html", {
        "task": task,
        "complete_form": form,
    })
