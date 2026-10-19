from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, AuditLog, UserRole
from .forms import CustomLoginForm, UserProfileForm, UserAdminCreateForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            AuditLog.objects.create(
                user=user,
                action="USER_LOGIN",
                ip_address=request.META.get("REMOTE_ADDR"),
                details=f"User {user.username} logged into dashboard"
            )
            messages.success(request, f"स्वागत है, {user.get_full_name() or user.username}!")
            next_url = request.GET.get("next") or "dashboard:index"
            return redirect(next_url)
        else:
            messages.error(request, "अमान्य उपयोगकर्ता नाम या पासवर्ड। कृपया पुनः प्रयास करें।")
    else:
        form = CustomLoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if request.user.is_authenticated:
        AuditLog.objects.create(
            user=request.user,
            action="USER_LOGOUT",
            ip_address=request.META.get("REMOTE_ADDR"),
            details=f"User {request.user.username} logged out"
        )
    logout(request)
    messages.info(request, "आप सफलतापूर्वक लॉग आउट हो गए हैं।")
    return redirect("public:home")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "प्रोफाइल सफलतापूर्वक अपडेट हो गई।")
            return redirect("accounts:profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


@login_required
def dashboard_users_list(request):
    if not request.user.is_super_admin:
        messages.error(request, "Only Super Admin can manage system users.")
        return redirect("dashboard:index")

    users = CustomUser.objects.all().order_by("-date_joined")
    if request.method == "POST":
        form = UserAdminCreateForm(request.POST)
        if form.is_valid():
            new_u = form.save()
            if new_u.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT", "PROJECT_MANAGER"]:
                new_u.is_staff = True
                new_u.save()
            messages.success(request, f"नया उपयोगकर्ता '{new_u.username}' सफलतापूर्वक बनाया गया।")
            return redirect("accounts:dashboard_users")
    else:
        form = UserAdminCreateForm()

    return render(request, "dashboard/accounts_users.html", {
        "users": users,
        "form": form,
    })


@login_required
def dashboard_audit_logs_view(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "TREASURER"]):
        messages.error(request, "Access restricted.")
        return redirect("dashboard:index")

    logs = AuditLog.objects.select_related("user").all()[:100]
    return render(request, "dashboard/audit_logs.html", {"logs": logs})
