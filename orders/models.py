from decimal import Decimal

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from accounts.models import Account, Address
from store.models import Coupon, Product, Variation


class Payment(models.Model):
    PROVIDER_COD = "cod"
    PROVIDER_EASYPAISA = "easypaisa"
    PROVIDER_JAZZCASH = "jazzcash"
    PROVIDER_CHOICES = (
        (PROVIDER_COD, "Cash on Delivery"),
        (PROVIDER_EASYPAISA, "Easypaisa"),
        (PROVIDER_JAZZCASH, "JazzCash"),
    )

    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="payments")
    payment_id = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=PROVIDER_COD)
    amount_payed = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100)
    mobile_account_phone = models.CharField(max_length=20, blank=True)
    proof_image = models.ImageField(upload_to="payments/proofs/", blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.payment_id


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    PAYMENT_STATUS_UNPAID = "unpaid"
    PAYMENT_STATUS_PENDING_VERIFICATION = "pending_verification"
    PAYMENT_STATUS_PAID = "paid"
    PAYMENT_STATUS_FAILED = "failed"
    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_STATUS_UNPAID, "Unpaid"),
        (PAYMENT_STATUS_PENDING_VERIFICATION, "Pending Verification"),
        (PAYMENT_STATUS_PAID, "Paid"),
        (PAYMENT_STATUS_FAILED, "Failed"),
    )

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="orders")
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True, related_name="orders")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, blank=True, null=True, related_name="orders")
    billing_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="billing_orders",
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="shipping_orders",
    )
    order_number = models.CharField(max_length=32, unique=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    carrier_name = models.CharField(max_length=100, default="Standard Delivery")
    payment_method = models.CharField(max_length=30, blank=True)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_UNPAID)
    mobile_account_phone = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20, blank=True)
    shipping_address_text = models.TextField(blank=True)
    order_note = models.CharField(max_length=100, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    order_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "is_ordered"]),
        ]

    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def full_address(self):
        return ", ".join(part for part in [self.address_line_1, self.address_line_2] if part)

    def generate_order_number(self):
        if not self.pk:
            return ""
        date_prefix = timezone.localdate(self.created_at or timezone.now()).strftime("%Y%m%d")
        return f"{date_prefix}{self.pk:06d}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
            super().save(update_fields=["order_number"])

    def __str__(self):
        return self.order_number or self.full_name()

    @property
    def payment_method_label(self):
        if self.payment and self.payment.payment_method:
            return self.payment.payment_method
        return self.payment_method.replace("_", " ").title() if self.payment_method else "N/A"


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True, related_name="order_items")
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_items")
    variation = models.ForeignKey(Variation, on_delete=models.SET_NULL, blank=True, null=True)
    variations = models.ManyToManyField(Variation, blank=True, related_name="order_items")
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.product.product_name

    def subtotal(self):
        return self.product_price * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"


def sync_order_status_history(order):
    latest = order.status_history.order_by("-created_at").first()
    if latest and latest.status == order.status:
        return
    OrderStatusHistory.objects.create(
        order=order,
        status=order.status,
        note=order.get_status_display(),
    )


@receiver(post_save, sender=Order)
def ensure_status_history(sender, instance, **kwargs):
    sync_order_status_history(instance)
