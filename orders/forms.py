from django import forms

from accounts.models import Address
from store.models import Coupon

from .models import Order


class OrderForm(forms.ModelForm):
    PAYMENT_METHOD_CHOICES = (
        ("cod", "Cash on Delivery"),
        ("easypaisa", "Easypaisa"),
        ("jazzcash", "JazzCash"),
    )

    billing_address_id = forms.ModelChoiceField(queryset=Address.objects.none(), required=False, empty_label="New billing address")
    shipping_address_id = forms.ModelChoiceField(queryset=Address.objects.none(), required=False, empty_label="New shipping address")
    same_as_billing = forms.BooleanField(required=False, initial=True)
    save_address = forms.BooleanField(required=False, initial=True)
    coupon_code = forms.CharField(required=False, max_length=30)
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, widget=forms.RadioSelect, initial="cod")
    mobile_account_phone = forms.CharField(required=False, max_length=20)
    transaction_id = forms.CharField(required=False, max_length=100)
    payment_proof = forms.ImageField(required=False)

    class Meta:
        model = Order
        fields = [
            "first_name",
            "last_name",
            "phone",
            "email",
            "address_line_1",
            "address_line_2",
            "country",
            "state",
            "city",
            "postal_code",
            "order_note",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            addresses = user.addresses.filter(is_active=True)
            self.fields["billing_address_id"].queryset = addresses
            self.fields["shipping_address_id"].queryset = addresses
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            if field_name in {"same_as_billing", "save_address"}:
                field.widget.attrs["class"] = "form-check-input"
            if field_name == "payment_method":
                field.widget.attrs["class"] = "custom-control-input"

    def clean_coupon_code(self):
        code = self.cleaned_data.get("coupon_code", "").strip()
        if code and not Coupon.objects.filter(code__iexact=code, is_active=True).exists():
            raise forms.ValidationError("This coupon code is invalid.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
        mobile_account_phone = cleaned_data.get("mobile_account_phone", "").strip()
        transaction_id = cleaned_data.get("transaction_id", "").strip()
        payment_proof = cleaned_data.get("payment_proof")

        if payment_method in {"easypaisa", "jazzcash"}:
            if not mobile_account_phone:
                self.add_error("mobile_account_phone", "A mobile account phone number is required for this payment method.")
            if not transaction_id and not payment_proof:
                message = "Provide a transaction ID or upload a payment screenshot for manual verification."
                self.add_error("transaction_id", message)
                self.add_error("payment_proof", message)

        return cleaned_data
