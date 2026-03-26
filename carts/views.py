from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from orders.forms import OrderForm
from store.models import Product, Variation

from .models import Cart, CartItem


TAX_RATE = Decimal("0.02")


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        request.session.create()
        cart = request.session.session_key
    return cart


def get_cart_items(request):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user, is_active=True).select_related("product").prefetch_related("variations")

    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    if not cart:
        return CartItem.objects.none()
    return CartItem.objects.filter(cart=cart, is_active=True).select_related("product").prefetch_related("variations")


def build_cart_summary(cart_items):
    subtotal = Decimal("0.00")
    quantity = 0
    for cart_item in cart_items:
        subtotal += cart_item.sub_total()
        quantity += cart_item.quantity
    tax = (subtotal * TAX_RATE).quantize(Decimal("0.01")) if subtotal else Decimal("0.00")
    grand_total = subtotal + tax
    return {
        "subtotal": subtotal,
        "total": subtotal,
        "quantity": quantity,
        "tax": tax,
        "grand_total": grand_total,
    }


def _selected_variations(product, post_data):
    product_variation = []
    for key, value in post_data.items():
        if key == "csrfmiddlewaretoken":
            continue
        try:
            variation = Variation.objects.get(
                product=product,
                variation_category__name__iexact=key,
                variation_value__iexact=value,
                is_active=True,
            )
            product_variation.append(variation)
        except Variation.DoesNotExist:
            continue
    return product_variation


def _find_existing_cart_item(items, product_variation, product_id):
    variation_ids = sorted(variation.id for variation in product_variation)
    for item in items:
        existing_ids = sorted(item.variations.values_list("id", flat=True))
        if item.product_id == product_id and existing_ids == variation_ids:
            return item
    return None


@require_POST
def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    product_variation = _selected_variations(product, request.POST)

    if request.user.is_authenticated:
        existing_items = CartItem.objects.filter(product=product, user=request.user).prefetch_related("variations")
        cart_item = _find_existing_cart_item(existing_items, product_variation, product.id)
        if cart_item:
            cart_item.quantity += 1
            cart_item.save(update_fields=["quantity"])
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, user=request.user)
            if product_variation:
                cart_item.variations.add(*product_variation)
    else:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
        existing_items = CartItem.objects.filter(product=product, cart=cart).prefetch_related("variations")
        cart_item = _find_existing_cart_item(existing_items, product_variation, product.id)
        if cart_item:
            cart_item.quantity += 1
            cart_item.save(update_fields=["quantity"])
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if product_variation:
                cart_item.variations.add(*product_variation)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        cart_items = get_cart_items(request)
        summary = build_cart_summary(cart_items)
        return JsonResponse(
            {
                "success": True,
                "product_name": product.product_name,
                "product_price": str(product.effective_price),
                "quantity_added": 1,
                "cart_total_price": str(summary["subtotal"]),
                "image_url": product.main_image.url if product.main_image else "",
                "cart_count": summary["quantity"],
            }
        )
    return redirect("cart")


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save(update_fields=["quantity"])
        else:
            cart_item.delete()
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        pass
    return redirect("cart")


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect("cart")


def cart(request):
    cart_items = get_cart_items(request)
    context = {
        "cart_items": cart_items,
        **build_cart_summary(cart_items),
    }
    return render(request, "store/cart.html", context)


@login_required(login_url="login")
def checkout(request):
    cart_items = get_cart_items(request)
    if not cart_items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect("store")

    summary = build_cart_summary(cart_items)
    initial = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
        "phone": request.user.phone_number,
    }
    default_address = request.user.addresses.filter(is_default=True, is_active=True).first()
    if default_address:
        initial.update(
            {
                "address_line_1": default_address.address_line_1,
                "address_line_2": default_address.address_line_2,
                "city": default_address.city,
                "state": default_address.state,
                "postal_code": default_address.postal_code,
                "country": default_address.country,
                "billing_address_id": default_address.id,
                "shipping_address_id": default_address.id,
            }
        )

    form = OrderForm(user=request.user, initial=initial)
    context = {
        "cart_items": cart_items,
        "order_form": form,
        "addresses": request.user.addresses.filter(is_active=True),
        **summary,
    }
    return render(request, "store/checkout.html", context)
