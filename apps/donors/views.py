from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum

from .models import Donor
from .forms import DonorForm
from apps.donations.models import Donation, PaymentStatus


@login_required
def dashboard_donor_list(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    qs = Donor.objects.all().order_by("-created_at")
    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(address__icontains=search)
        )

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "dashboard/donors/list.html", {
        "page_obj": page_obj,
        "search": search,
        "total_donors": Donor.objects.count(),
    })


@login_required
def dashboard_donor_detail(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    donations = donor.donations.all().order_by("-donation_date", "-created_at")
    total_given = donations.filter(payment_status=PaymentStatus.CONFIRMED).aggregate(s=Sum("amount"))["s"] or 0

    return render(request, "dashboard/donors/detail.html", {
        "donor": donor,
        "donations": donations,
        "total_given": total_given,
    })


@login_required
def dashboard_donor_create(request):
    if not request.user.can_manage_finances:
        messages.error(request, "Only finance managers can add donors.")
        return redirect("donors:dashboard_list")

    if request.method == "POST":
        form = DonorForm(request.POST)
        if form.is_valid():
            donor = form.save()
            messages.success(request, f"दानदाता '{donor.name}' का प्रोफाइल दर्ज किया गया।")
            return redirect("donors:dashboard_detail", pk=donor.pk)
    else:
        form = DonorForm()

    return render(request, "dashboard/donors/form.html", {
        "form": form,
        "title": "नया दानदाता प्रोफाइल जोड़ें",
    })


@login_required
def dashboard_donor_edit(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    if not request.user.can_manage_finances:
        messages.error(request, "Access restricted.")
        return redirect("donors:dashboard_detail", pk=pk)

    if request.method == "POST":
        form = DonorForm(request.POST, instance=donor)
        if form.is_valid():
            donor = form.save()
            messages.success(request, f"दानदाता '{donor.name}' का विवरण अपडेट किया गया।")
            return redirect("donors:dashboard_detail", pk=donor.pk)
    else:
        form = DonorForm(instance=donor)

    return render(request, "dashboard/donors/form.html", {
        "form": form,
        "donor": donor,
        "title": f"दानदाता विवरण संपादित करें: {donor.name}",
    })
