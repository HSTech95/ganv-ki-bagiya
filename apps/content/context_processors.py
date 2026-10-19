from .models import SiteSetting


def site_settings(request):
    try:
        settings = SiteSetting.load()
    except Exception:
        settings = None
    return {
        "site_settings": settings,
        "SITE_TITLE": "गाँव की बगिया | Ganv Ki Bagiya",
    }
