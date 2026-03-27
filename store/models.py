from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import Account
from category.models import Category


try:
    RESAMPLING_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # Pillow < 9.1
    RESAMPLING_LANCZOS = Image.LANCZOS


def optimize_image_field(image_field, max_size=(1400, 1400), quality=82):
    if not image_field or not getattr(image_field, "name", None):
        return

    try:
        image_field.open("rb")
        image = Image.open(image_field)
        image.load()
    except Exception:
        return

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    image.thumbnail(max_size, RESAMPLING_LANCZOS)
    output = BytesIO()
    image.save(output, format="JPEG", optimize=True, quality=quality)
    output.seek(0)

    original_name = Path(image_field.name).stem
    image_field.save(f"{original_name}.jpg", ContentFile(output.read()), save=False)


class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True, db_index=True)
    main_image = models.ImageField(
        upload_to="photos/products",
        help_text="Main product image",
        null=True,
        blank=True,
    )
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("product_name",)
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["product_name"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["brand"]),
        ]

    def get_url(self):
        return reverse("product_detail", args=[self.category.slug, self.slug])

    @property
    def stock_count(self):
        return self.stock

    @property
    def effective_price(self):
        if self.has_discount:
            return self.discount_price
        return self.price

    @property
    def has_discount(self):
        return (
            self.discount_price is not None
            and self.discount_price > Decimal("0")
            and self.discount_price < self.price
        )

    @property
    def discount_percent(self):
        if not self.has_discount or self.price <= Decimal("0"):
            return 0
        percentage = ((self.price - self.discount_price) / self.price) * Decimal("100")
        return int(percentage.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @property
    def in_stock(self):
        return self.stock > 0 and self.is_active

    def __str__(self):
        return self.product_name

    def save(self, *args, **kwargs):
        self.is_available = self.is_active
        optimize_image_field(self.main_image)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="photos/products")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of display (0 = first)")
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_date"]

    def __str__(self):
        return f"{self.product.product_name} - Image {self.order + 1}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f"{self.product.product_name} - Image {self.order + 1}"
        optimize_image_field(self.image)
        super().save(*args, **kwargs)


class VariationCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Internal name (e.g., 'color', 'size')")
    display_name = models.CharField(max_length=100, help_text="Display name (e.g., 'Color', 'Size')")
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Variation Category"
        verbose_name_plural = "Variation Categories"
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class VariationManager(models.Manager):
    def get_variations_by_category(self, category_name):
        return self.filter(variation_category__name=category_name, is_active=True)

    def colors(self):
        return self.get_variations_by_category("color")

    def sizes(self):
        return self.get_variations_by_category("size")


class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variations")
    variation_category = models.ForeignKey(VariationCategory, on_delete=models.CASCADE, related_name="variations")
    variation_value = models.CharField(max_length=100, db_index=True)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    class Meta:
        unique_together = ("product", "variation_category", "variation_value")
        ordering = ["variation_category__display_name", "variation_value"]

    def __str__(self):
        return f"{self.product.product_name} - {self.variation_category.display_name}: {self.variation_value}"


class Coupon(models.Model):
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    DISCOUNT_TYPE_CHOICES = (
        (PERCENTAGE, "Percentage"),
        (FIXED, "Fixed"),
    )

    code = models.CharField(max_length=30, unique=True, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default=PERCENTAGE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return self.code

    def is_valid_for_total(self, total, now=None):
        now = now or timezone.now()
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at <= now:
            return False
        if self.used_count >= self.usage_limit:
            return False
        return total >= self.minimum_order_amount

    def get_discount_amount(self, subtotal):
        if subtotal <= 0:
            return Decimal("0.00")

        if self.discount_type == self.PERCENTAGE:
            discount = (subtotal * self.amount) / Decimal("100")
        else:
            discount = self.amount

        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        return max(Decimal("0.00"), min(discount, subtotal))


class WishlistItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist_items")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} -> {self.product.product_name}"


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.product.product_name} review by {self.user.email}"
