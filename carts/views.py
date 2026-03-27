from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from orders.forms import OrderForm
from store.models import Product, Variation

from .models import Cart, CartItem


TAX_RATE = Decimal("0.02")
SHIPPING_RATE = Decimal("0.00")


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
    shipping = SHIPPING_RATE if subtotal else Decimal("0.00")
    grand_total = subtotal + tax + shipping
    return {
        "subtotal": subtotal,
        "cart_total": subtotal,
        "total": subtotal,
        "quantity": quantity,
        "tax": tax,
        "shipping": shipping,
        "grand_total": grand_total,
    }


def _format_money(value):
    return format(value.quantize(Decimal("0.01")), ".2f")


def _parse_quantity(value, default=1):
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, quantity)


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


def _get_cart_item_for_request(request, cart_item_id):
    queryset = CartItem.objects.select_related("product").prefetch_related("variations")
    if request.user.is_authenticated:
        return get_object_or_404(queryset, id=cart_item_id, user=request.user, is_active=True)

    cart = get_object_or_404(Cart, cart_id=_cart_id(request))
    return get_object_or_404(queryset, id=cart_item_id, cart=cart, is_active=True)


def _cart_item_payload(request, cart_item=None, *, item_removed=False, message=""):
    cart_items = get_cart_items(request)
    summary = build_cart_summary(cart_items)
    payload = {
        "success": True,
        "message": message,
        "item_removed": item_removed,
        "cart_empty": summary["quantity"] == 0,
        "cart_count": summary["quantity"],
        "cart_total": _format_money(summary["subtotal"]),
        "tax": _format_money(summary["tax"]),
        "shipping": _format_money(summary["shipping"]),
        "grand_total": _format_money(summary["grand_total"]),
    }
    if cart_item is not None and not item_removed:
        payload.update(
            {
                "item_id": cart_item.id,
                "quantity": cart_item.quantity,
                "item_subtotal": _format_money(cart_item.sub_total()),
                "product_price": _format_money(cart_item.product.effective_price),
                "max_quantity": cart_item.product.stock_count,
            }
        )
    else:
        payload.update(
            {
                "item_id": cart_item.id if cart_item else None,
                "quantity": 0,
                "item_subtotal": "0.00",
            }
        )
    if payload["cart_empty"]:
        payload["empty_cart_html"] = render_to_string("store/partials/cart_empty_state.html", request=request)
    return payload


@require_POST
def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    product_variation = _selected_variations(product, request.POST)
    requested_quantity = _parse_quantity(request.POST.get("quantity"), default=1)

    if product.stock_count <= 0:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": "This item is currently out of stock."}, status=400)
        messages.error(request, "This item is currently out of stock.")
        return redirect(product.get_url())

    if request.user.is_authenticated:
        existing_items = CartItem.objects.filter(product=product, user=request.user).prefetch_related("variations")
        cart_item = _find_existing_cart_item(existing_items, product_variation, product.id)
        if cart_item:
            previous_quantity = cart_item.quantity
            cart_item.quantity = min(product.stock_count, cart_item.quantity + requested_quantity)
            cart_item.save(update_fields=["quantity"])
        else:
            previous_quantity = 0
            cart_item = CartItem.objects.create(
                product=product,
                quantity=min(product.stock_count, requested_quantity),
                user=request.user,
            )
            if product_variation:
                cart_item.variations.add(*product_variation)
    else:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
        existing_items = CartItem.objects.filter(product=product, cart=cart).prefetch_related("variations")
        cart_item = _find_existing_cart_item(existing_items, product_variation, product.id)
        if cart_item:
            previous_quantity = cart_item.quantity
            cart_item.quantity = min(product.stock_count, cart_item.quantity + requested_quantity)
            cart_item.save(update_fields=["quantity"])
        else:
            previous_quantity = 0
            cart_item = CartItem.objects.create(
                product=product,
                quantity=min(product.stock_count, requested_quantity),
                cart=cart,
            )
            if product_variation:
                cart_item.variations.add(*product_variation)

    quantity_added = cart_item.quantity - previous_quantity
    if quantity_added <= 0:
        message = "You already have the maximum available quantity in your cart."
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": message, "cart_count": build_cart_summary(get_cart_items(request))["quantity"]}, status=400)
        messages.info(request, message)
        return redirect("cart")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        cart_items = get_cart_items(request)
        summary = build_cart_summary(cart_items)
        return JsonResponse(
            {
                "success": True,
                "product_name": product.product_name,
                "product_price": _format_money(product.effective_price),
                "quantity_added": quantity_added,
                "cart_total_price": _format_money(summary["subtotal"]),
                "image_url": product.main_image.url if product.main_image else "",
                "cart_count": summary["quantity"],
                "tax": _format_money(summary["tax"]),
                "shipping": _format_money(summary["shipping"]),
                "grand_total": _format_money(summary["grand_total"]),
                "message": "Cart updated successfully.",
            }
        )
    return redirect("cart")


@require_POST
def update_cart_item(request, cart_item_id):
    cart_item = _get_cart_item_for_request(request, cart_item_id)
    action = request.POST.get("action", "set")
    product = cart_item.product
    previous_quantity = cart_item.quantity

    if action == "increment":
        new_quantity = min(previous_quantity + 1, product.stock_count)
    elif action == "decrement":
        new_quantity = previous_quantity - 1
    elif action == "remove":
        new_quantity = 0
    else:
        new_quantity = min(_parse_quantity(request.POST.get("quantity"), default=previous_quantity), product.stock_count)

    if action == "increment" and new_quantity == previous_quantity:
        payload = _cart_item_payload(
            request,
            cart_item,
            message="You have reached the maximum stock available for this item.",
        )
        payload["success"] = False
        return JsonResponse(payload, status=400)

    if new_quantity <= 0:
        removed_item_id = cart_item.id
        cart_item.delete()
        payload = _cart_item_payload(request, message="Item removed from cart.", item_removed=True)
        payload["item_id"] = removed_item_id
        return JsonResponse(payload)

    cart_item.quantity = new_quantity
    cart_item.save(update_fields=["quantity"])
    message = "Cart updated successfully." if new_quantity != previous_quantity else ""
    return JsonResponse(_cart_item_payload(request, cart_item, message=message))


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
