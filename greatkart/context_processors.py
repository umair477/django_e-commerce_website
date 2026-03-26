from django.conf import settings


def site_meta(request):
    return {
        "site_name": settings.SITE_NAME,
        "site_description": settings.SITE_DESCRIPTION,
        "site_domain": settings.SITE_DOMAIN,
    }
