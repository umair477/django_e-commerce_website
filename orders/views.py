from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView

from accounts.models import Address
from carts.models import CartItem
from carts.views import build_cart_summary, get_cart_items
from store.models import Coupon

from .forms import OrderForm
from .models import Order, OrderProduct, Payment
from .utils import build_simple_invoice_pdf, send_order_invoice


LOCAL_PAYMENT_LABELS = {
    "cod": "Cash on Delivery",
    "easypaisa": "Easypaisa",
    "jazzcash": "JazzCash",
}


def _create_or_update_address_from_form(user, cleaned_data):
    full_name = f'{cleaned_data["first_name"]} {cleaned_data["last_name"]}'.strip()
    return Address.objects.create(
        user=user,
        label="Checkout",
        full_name=full_name,
        phone_number=cleaned_data["phone"],
        address_line_1=cleaned_data["address_line_1"],
        address_line_2=cleaned_data["address_line_2"],
        city=cleaned_data["city"],
        state=cleaned_data["state"],
        postal_code=cleaned_data["postal_code"],
        country=cleaned_data["country"],
        address_type=Address.BOTH,
        is_default=cleaned_data.get("save_address", False),
    )


def _selected_coupon(code):
    if not code:
        return None
    coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
    if coupon and coupon.expires_at and coupon.expires_at <= timezone.now():
        return None
    return coupon


def _build_order_items(order, cart_items, payment=None):
    for item in cart_items:
        order_product = OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=order.user,
            product=item.product,
            variation=item.variations.first(),
            color=", ".join(
                item.variations.filter(variation_category__name__iexact="color").values_list("variation_value", flat=True)
            ),
            size=", ".join(
                item.variations.filter(variation_category__name__iexact="size").values_list("variation_value", flat=True)
            ),
            quantity=item.quantity,
            product_price=item.product.effective_price,
            ordered=True,
        )
        if item.variations.exists():
            order_product.variations.add(*item.variations.all())

        product = item.product
        product.stock = max(0, product.stock - item.quantity)
        product.is_active = product.stock > 0
        product.save(update_fields=["stock", "is_active", "is_available", "modified_date"])


def _finalize_order(order, cart_items, payment=None):
    _build_order_items(order, cart_items, payment=payment)
    if order.coupon:
        order.coupon.used_count += 1
        order.coupon.save(update_fields=["used_count"])
    cart_items.delete()
    send_order_invoice(order)


def _matching_cart_item(user, product, variation_ids):
    cart_items = CartItem.objects.filter(user=user, product=product).prefetch_related("variations")
    for cart_item in cart_items:
        existing_ids = sorted(cart_item.variations.values_list("id", flat=True))
        if existing_ids == sorted(variation_ids):
            return cart_item
    return None


@login_required(login_url="login")
def place_order(request):
    cart_items = get_cart_items(request)
    if not cart_items.exists():
        return redirect("store")

    summary = build_cart_summary(cart_items)

    if request.method != "POST":
        return redirect("checkout")

    form = OrderForm(request.POST, request.FILES, user=request.user)
    if not form.is_valid():
        return render(
            request,
            "store/checkout.html",
            {
                "cart_items": cart_items,
                "order_form": form,
                "addresses": request.user.addresses.filter(is_active=True),
                **summary,
            },
        )

    cleaned = form.cleaned_data
    billing_address = cleaned.get("billing_address_id")
    shipping_address = cleaned.get("shipping_address_id")
    if not billing_address:
        billing_address = _create_or_update_address_from_form(request.user, cleaned) if cleaned.get("save_address") else None
    if cleaned.get("same_as_billing"):
        shipping_address = billing_address

    coupon = _selected_coupon(cleaned.get("coupon_code"))
    discount_total = coupon.get_discount_amount(summary["subtotal"]) if coupon else Decimal("0.00")
    order_total = summary["subtotal"] + summary["tax"] - discount_total
    payment_method = cleaned["payment_method"]
    mobile_account_phone = cleaned.get("mobile_account_phone", "").strip()

    order = Order.objects.create(
        user=request.user,
        coupon=coupon,
        billing_address=billing_address,
        shipping_address=shipping_address,
        payment_method=payment_method,
        mobile_account_phone=mobile_account_phone,
        first_name=cleaned["first_name"],
        last_name=cleaned["last_name"],
        email=cleaned["email"],
        phone=cleaned["phone"],
        address_line_1=cleaned["address_line_1"],
        address_line_2=cleaned["address_line_2"],
        city=cleaned["city"],
        state=cleaned["state"],
        country=cleaned["country"],
        postal_code=cleaned["postal_code"],
        shipping_address_text=shipping_address.full_address() if shipping_address else "",
        order_note=cleaned["order_note"],
        subtotal=summary["subtotal"],
        discount_total=discount_total,
        tax=summary["tax"],
        order_total=order_total,
        ip=request.META.get("REMOTE_ADDR", ""),
    )

    if payment_method == Payment.PROVIDER_COD:
        payment = Payment.objects.create(
            user=request.user,
            payment_id=f"COD-{order.order_number}",
            payment_method=LOCAL_PAYMENT_LABELS[payment_method],
            provider=Payment.PROVIDER_COD,
            amount_payed=Decimal("0.00"),
            status=Order.PAYMENT_STATUS_UNPAID,
            notes="Cash will be collected on delivery.",
        )
        order.payment = payment
        order.payment_status = Order.PAYMENT_STATUS_UNPAID
        order.status = Order.STATUS_PENDING
        order.is_ordered = True
        order.save(update_fields=["payment", "payment_status", "status", "is_ordered", "updated_at"])
        _finalize_order(order, cart_items, payment=payment)
        messages.success(request, "Your cash on delivery order has been placed successfully.")
        return redirect("account_orders")

    payment = Payment.objects.create(
        user=request.user,
        payment_id=f"{payment_method.upper()}-{order.order_number}",
        transaction_id=cleaned.get("transaction_id", "").strip(),
        payment_method=LOCAL_PAYMENT_LABELS[payment_method],
        provider=payment_method,
        amount_payed=Decimal("0.00"),
        status=Order.PAYMENT_STATUS_PENDING_VERIFICATION,
        mobile_account_phone=mobile_account_phone,
        proof_image=cleaned.get("payment_proof"),
        notes="Awaiting admin verification.",
    )
    order.payment = payment
    order.transaction_id = payment.transaction_id
    order.payment_status = Order.PAYMENT_STATUS_PENDING_VERIFICATION
    order.status = Order.STATUS_PENDING
    order.is_ordered = True
    order.save(
        update_fields=[
            "payment",
            "transaction_id",
            "payment_status",
            "status",
            "is_ordered",
            "updated_at",
        ]
    )
    _finalize_order(order, cart_items, payment=payment)
    messages.success(
        request,
        f"Your {LOCAL_PAYMENT_LABELS[payment_method]} payment details were submitted and are pending verification.",
    )
    return redirect("account_orders")


@login_required(login_url="login")
def invoice(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        order_number=order_number,
        user=request.user,
    )
    pdf = build_simple_invoice_pdf(order)
    return FileResponse(pdf, as_attachment=True, filename=f"invoice-{order.order_number}.pdf")


class OrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    pk_url_kwarg = "order_id"

    def get_queryset(self):
        return (
            Order.objects.select_related("payment", "shipping_address", "billing_address")
            .prefetch_related("items__product", "items__variations", "status_history")
            .all()
        )

    def test_func(self):
        return self.get_object().user_id == self.request.user.id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_updates"] = self.object.status_history.all()
        return context


@login_required(login_url="login")
def reorder(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product", "items__variations"),
        pk=order_id,
        user=request.user,
    )

    for item in order.items.all():
        variation_ids = list(item.variations.values_list("id", flat=True))
        cart_item = _matching_cart_item(request.user, item.product, variation_ids)
        if cart_item:
            cart_item.quantity += item.quantity
            cart_item.save(update_fields=["quantity"])
            continue

        cart_item = CartItem.objects.create(user=request.user, product=item.product, quantity=item.quantity)
        if variation_ids:
            cart_item.variations.add(*item.variations.all())

    messages.success(request, "The order items have been added back to your cart.")
    return redirect("cart")
