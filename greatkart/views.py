from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from store.models import Product


def home(request):
    products = (
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .order_by("-created_date")[:8]
    )
    context = {
        "products": products,
        "meta_title": settings.SITE_NAME,
        "meta_description": settings.SITE_DESCRIPTION,
    }
    return render(request, "home.html", context)


def healthz(request):
    return JsonResponse({"status": "ok"})
