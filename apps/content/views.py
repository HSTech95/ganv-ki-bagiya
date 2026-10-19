# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from django.contrib import messages
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
from .models import Announcement, VolunteerRegistration, ContactSubmission, SiteSetting
from .forms import ContactForm, VolunteerForm, SiteSettingForm
from apps.donations.models import Donation, PaymentStatus
from apps.finance.services import get_financial_summary
from apps.projects.models import Project, ProjectStatus
from apps.gallery.models import GalleryItem, GalleryAlbum
from apps.maintenance.models import MaintenanceTask


def home(request):
    financial_data = get_financial_summary()
    active_projects = Project.objects.filter(is_public=True, status=ProjectStatus.ACTIVE)[:4]
    announcements = Announcement.objects.filter(is_active=True)[:5]
    before_after_items = GalleryItem.objects.filter(is_before_after=True)[:4]
    gallery_preview = GalleryItem.objects.filter(is_before_after=False)[:6]
    recent_tasks = MaintenanceTask.objects.order_by("-scheduled_date")[:4]

    # Recent public donations for public dashboard visibility
    recent_donations = Donation.objects.filter(
        payment_status__in=[PaymentStatus.CONFIRMED, PaymentStatus.PENDING]
    ).select_related("donor", "related_project").order_by("-donation_date", "-created_at")[:8]

    contact_form = ContactForm()
    volunteer_form = VolunteerForm()

    context = {
        "stats": financial_data,
        "recent_donations": recent_donations,
        "active_projects": active_projects,
        "announcements": announcements,
        "before_after_items": before_after_items,
        "gallery_preview": gallery_preview,
        "recent_tasks": recent_tasks,
        "contact_form": contact_form,
        "volunteer_form": volunteer_form,
    }
    return render(request, "public/index.html", context)


def about(request):
    settings = SiteSetting.load()
    projects = Project.objects.filter(is_public=True)
    context = {
        "site_settings": settings,
        "projects": projects,
    }
    return render(request, "public/about.html", context)


def contact(request):
    
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "आपका संदेश सफलतापूर्वक प्राप्त हो गया है। समिति के सदस्य शीघ्र ही आपसे संपर्क करेंगे।"
            )
            return redirect("public:contact")
        else:
            messages.error(request, "कृपया प्रपत्र में दिए गए विवरणों को सही से भरें।")
    else:
        form = ContactForm()

    settings = SiteSetting.load()
    return render(request, "public/contact.html", {"form": form, "site_settings": settings})


def volunteer_register(request):
    if request.method == "POST":
        form = VolunteerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "गाँव की बगिया व कब्रिस्तान सेवा अभियान से जुड़ने के लिए आपका बहुत-बहुत धन्यवाद! समिति आपको सेवा कार्यों में आमंत्रित करेगी।"
            )
            return redirect("public:home")
        else:
            messages.error(request, "कृपया सही जानकारी दर्ज करें।")
    else:
        form = VolunteerForm()
    return render(request, "public/volunteer.html", {"form": form})


# Staff Dashboard Content Views
@login_required
def dashboard_inquiries(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "TREASURER"]):
        messages.error(request, "Unauthorized access.")
        return redirect("public:home")

    submissions = ContactSubmission.objects.all()
    volunteers = VolunteerRegistration.objects.all()
    announcements = Announcement.objects.all()

    return render(request, "dashboard/inquiries.html", {
        "submissions": submissions,
        "volunteers": volunteers,
        "announcements": announcements,
    })


@login_required
def resolve_inquiry(request, pk):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT"]):
        messages.error(request, "Unauthorized access.")
        return redirect("public:home")

    item = get_object_or_404(ContactSubmission, pk=pk)
    if request.method == "POST":
        notes = request.POST.get("notes", "")
        item.is_resolved = True
        item.resolution_notes = notes
        item.save()
        messages.success(request, f"Inquiry #{item.id} marked as resolved.")
    return redirect("content:dashboard_inquiries")


@login_required
def dashboard_settings(request):
    if not request.user.is_super_admin:
        messages.error(request, "Only Super Admin can edit global settings.")
        return redirect("dashboard:index")

    setting_obj = SiteSetting.load()
    if request.method == "POST":
        form = SiteSettingForm(request.POST, instance=setting_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Site settings updated successfully.")
            return redirect("content:dashboard_settings")
    else:
        form = SiteSettingForm(instance=setting_obj)

    return render(request, "dashboard/settings.html", {"form": form})
