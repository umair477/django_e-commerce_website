from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category

from .filters import build_product_filter
from .models import Product, Review, VariationCategory, WishlistItem


def _base_product_queryset():
    return (
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .prefetch_related("images", "variations", "reviews")
    )


def _store_context(request, category_slug=None):
    category = None
    queryset = _base_product_queryset()

    if category_slug is not None:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        queryset = queryset.filter(category=category)

    keyword = request.GET.get("keyword", "").strip()
    if keyword:
        queryset = queryset.filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))

    filtered_products, filter_form = build_product_filter(queryset, request.GET)
    filtered_products = filtered_products.annotate(average_rating=Avg("reviews__rating")).order_by("product_name")

    paginator = Paginator(filtered_products, 6)
    page = request.GET.get("page")
    paged_products = paginator.get_page(page)

    filter_options = {
        "brands": list(queryset.exclude(brand="").values_list("brand", flat=True).distinct()),
        "sizes": list(
            queryset.filter(variations__variation_category__name__iexact="size")
            .values_list("variations__variation_value", flat=True)
            .distinct()
        ),
        "colors": list(
            queryset.filter(variations__variation_category__name__iexact="color")
            .values_list("variations__variation_value", flat=True)
            .distinct()
        ),
    }
    query_without_page = request.GET.copy()
    query_without_page.pop("page", None)

    return {
        "category": category,
        "products": paged_products,
        "product_count": filtered_products.count(),
        "filter_form": filter_form,
        "filter_options": filter_options,
        "keyword": keyword,
        "store_action_url": category.get_url() if category else reverse("store"),
        "base_querystring": query_without_page.urlencode(),
        "meta_title": category.catergory_name if category else _("Store"),
        "meta_description": category.description if category and category.description else settings.SITE_DESCRIPTION,
    }


def store(request, category_slug=None):
    context = _store_context(request, category_slug=category_slug)
    template_name = "store/partials/product_results.html"
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        template_name = "store/store.html"
    return render(request, template_name, context)


def product_detail(request, category_slug, product_slug):
    single_product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images", "variations", "reviews__user"),
        category__slug=category_slug,
        slug=product_slug,
        is_active=True,
    )
    in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    variation_categories = (
        VariationCategory.objects.filter(variations__product=single_product, variations__is_active=True, is_active=True)
        .distinct()
        .order_by("display_name")
    )
    product_images = single_product.images.filter(is_active=True).order_by("order", "created_date")
    reviews = single_product.reviews.filter(is_approved=True).select_related("user")
    is_wishlisted = False

    if request.user.is_authenticated:
        is_wishlisted = WishlistItem.objects.filter(user=request.user, product=single_product).exists()

    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "variation_categories": variation_categories,
        "product_images": product_images,
        "reviews": reviews,
        "is_wishlisted": is_wishlisted,
        "meta_title": single_product.product_name,
        "meta_description": single_product.description or settings.SITE_DESCRIPTION,
    }
    return render(request, "store/product_detail.html", context)


def search(request):
    return store(request)


@require_POST
@login_required(login_url="login")
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        wishlist_item.delete()
        wished = False
        message = _("Removed from wishlist.")
    else:
        wished = True
        message = _("Added to wishlist.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"wished": wished, "message": message})

    messages.success(request, message)
    return redirect(product.get_url())


@require_POST
@login_required(login_url="login")
def submit_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    rating = int(request.POST.get("rating", 5))
    review_text = request.POST.get("comment", "").strip()
    if not review_text:
        messages.error(request, "Please write a short review comment.")
        return redirect(product.get_url())

    Review.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={
            "rating": max(1, min(rating, 5)),
            "comment": review_text,
            "is_approved": True,
        },
    )
    messages.success(request, "Your review has been saved.")
    return redirect(product.get_url())
