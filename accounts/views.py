from urllib.parse import parse_qs, urlparse

from django.contrib import auth, messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import activate as activate_language
from django.views.decorators.http import require_POST

from carts.models import Cart, CartItem
from carts.views import _cart_id

from .forms import AddressForm, ProfileForm, RegistrationForm, StyledPasswordChangeForm
from .models import Account, Address


def _merge_guest_cart_with_user(request, user):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        return

    guest_items = CartItem.objects.filter(cart=cart).prefetch_related("variations")
    user_items = CartItem.objects.filter(user=user).prefetch_related("variations")

    existing_variations = {}
    for item in user_items:
        key = tuple(sorted(item.variations.values_list("id", flat=True)))
        existing_variations[key] = item

    for item in guest_items:
        key = tuple(sorted(item.variations.values_list("id", flat=True)))
        if key in existing_variations and existing_variations[key].product_id == item.product_id:
            existing = existing_variations[key]
            existing.quantity += item.quantity
            existing.save(update_fields=["quantity"])
            item.delete()
            continue
        item.user = user
        item.cart = None
        item.save(update_fields=["user", "cart"])


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = Account.objects.create_user(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=email,
                username=email.split("@")[0],
                password=form.cleaned_data["password"],
                phone_number=form.cleaned_data["phone_number"],
                preferred_language=form.cleaned_data["preferred_language"],
            )
            user.is_active = False
            user.save()

            message = render_to_string(
                "accounts/account_verification_email.html",
                {
                    "user": user,
                    "domain": request.get_host(),
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            EmailMessage("Please activate your account", message, to=[email]).send(fail_silently=True)
            return redirect("/accounts/login/?command=verification&email=" + email)
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = auth.authenticate(email=email, password=password)
        if user is None:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        _merge_guest_cart_with_user(request, user)
        auth.login(request, user)
        activate_language(getattr(user, "preferred_language", "en"))
        messages.success(request, "You are now logged in.")

        referrer = request.META.get("HTTP_REFERER", "")
        next_values = parse_qs(urlparse(referrer).query).get("next")
        if next_values:
            return redirect(next_values[0])
        return redirect("dashboard")

    return render(request, "accounts/login.html")


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out.")
    return redirect("login")


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, "Invalid activation link. Please try again.")
        return redirect("register")

    user.is_active = True
    user.email_verified = True
    user.save(update_fields=["is_active", "email_verified"])
    send_mail(
        "Welcome to GreatKart",
        f"Hi {user.first_name}, your account is now active and ready to shop.",
        None,
        [user.email],
        fail_silently=True,
    )
    messages.success(request, "Congratulations. Your account is activated.")
    return redirect("login")


@login_required(login_url="login")
def _dashboard_context(request, section, address_form=None, profile_form=None, password_form=None):
    orders = (
        request.user.orders.select_related("payment", "shipping_address", "billing_address")
        .prefetch_related("items__product", "items__variations")
        .all()
    )
    addresses = request.user.addresses.filter(is_active=True)

    edit_address = None
    edit_address_id = request.GET.get("edit")
    if edit_address_id and section == "addresses":
        edit_address = get_object_or_404(Address, pk=edit_address_id, user=request.user, is_active=True)

    context = {
        "orders": orders,
        "recent_orders": orders[:3],
        "addresses": addresses,
        "profile_form": profile_form or ProfileForm(instance=request.user),
        "password_form": password_form or StyledPasswordChangeForm(user=request.user),
        "address_form": address_form or AddressForm(instance=edit_address),
        "wishlist_items": request.user.wishlist_items.select_related("product", "product__category"),
        "active_section": section,
        "edit_address": edit_address,
    }
    return render(request, "accounts/dashboard.html", context)


@login_required(login_url="login")
def dashboard(request):
    return _dashboard_context(request, "overview")


@login_required(login_url="login")
def account_orders(request):
    return _dashboard_context(request, "orders")


@login_required(login_url="login")
def account_addresses(request):
    address_form = None
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete_address":
            address = get_object_or_404(Address, pk=request.POST.get("address_id"), user=request.user)
            address.is_active = False
            address.is_default = False
            address.save(update_fields=["is_active", "is_default"])
            messages.success(request, "Address removed.")
            return redirect("account_addresses")

        address_id = request.POST.get("address_id")
        instance = get_object_or_404(Address, pk=address_id, user=request.user) if address_id else None
        address_form = AddressForm(request.POST, instance=instance)
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address book updated.")
            return redirect("account_addresses")

    return _dashboard_context(request, "addresses", address_form=address_form)


@login_required(login_url="login")
def account_profile(request):
    profile_form = None
    password_form = None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "profile":
            profile_form = ProfileForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect("account_profile")

        elif action == "password":
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed.")
                return redirect("account_profile")

    return _dashboard_context(
        request,
        "profile",
        profile_form=profile_form,
        password_form=password_form,
    )


@require_POST
@login_required(login_url="login")
def delete_address(request, address_id):
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    address.is_active = False
    address.is_default = False
    address.save(update_fields=["is_active", "is_default"])
    messages.success(request, "Address removed.")
    return redirect("account_addresses")
