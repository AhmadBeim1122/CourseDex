from django.conf import settings

from .models import SiteSetting


def site_settings(request):
    """Makes site-wide settings & SEO config available in every template."""
    return {
        "site_settings": SiteSetting.load(),
        "SITE_NAME": settings.SITE_NAME,
        "SITE_INITIALS": settings.SITE_INITIALS,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "ADSENSE_CLIENT_ID": settings.ADSENSE_CLIENT_ID,
        "GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID,
        "GOOGLE_SITE_VERIFICATION": settings.GOOGLE_SITE_VERIFICATION,
    }
