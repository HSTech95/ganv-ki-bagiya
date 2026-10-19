# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.urls import path, include
# pyrefly: ignore [missing-import]
from django.conf import settings
# pyrefly: ignore [missing-import]
from django.conf.urls.static import static

from apps.content import views as content_views
from apps.accounts import dashboard_views

# Public website router
public_patterns = [
    path("", content_views.home, name="home"),
    path("about/", content_views.about, name="about"),
    path("contact/", content_views.contact, name="contact"),
    path("volunteer/", content_views.volunteer_register, name="volunteer"),
]

dashboard_patterns = [
    path("dashboard/", dashboard_views.dashboard_home, name="index"),
]

urlpatterns = [
    path("django-admin/", admin.site.urls),

    # Public Core
    path("", include((public_patterns, "public"), namespace="public")),

    # Dashboard Root
    path("", include((dashboard_patterns, "dashboard"), namespace="dashboard")),

    # Modular App URLs
    path("", include("apps.donations.urls")),
    path("", include("apps.donors.urls")),
    path("", include("apps.payments.urls")),
    path("", include("apps.finance.urls")),
    path("", include("apps.projects.urls")),
    path("", include("apps.expenses.urls")),
    path("", include("apps.maintenance.urls")),
    path("", include("apps.gallery.urls")),
    path("", include("apps.content.urls")),
    path("", include("apps.reports.urls")),
    path("", include("apps.accounts.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
