from django.contrib import admin

from .models import Coupon, Product, ProductImage, Review, Variation, VariationCategory, WishlistItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_active", "order")


@admin.register(VariationCategory)
class VariationCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_name", "is_active", "created_date")
    list_editable = ("is_active",)
    list_filter = ("is_active", "created_date")
    search_fields = ("name", "display_name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("product_name",)}
    list_display = ("product_name", "brand", "price", "discount_price", "stock", "category", "is_active")
    list_filter = ("is_active", "category", "brand")
    search_fields = ("product_name", "description", "brand")
    autocomplete_fields = ("category",)
    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text", "is_active", "order", "created_date")
    list_editable = ("is_active", "order")
    list_filter = ("is_active", "created_date", "product")
    search_fields = ("product__product_name", "alt_text")
    autocomplete_fields = ["product"]


@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ("product", "variation_category", "variation_value", "is_active")
    list_editable = ("is_active",)
    list_filter = ("product", "variation_category", "is_active")
    search_fields = ("product__product_name", "variation_value")
    autocomplete_fields = ["product", "variation_category"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "amount", "usage_limit", "used_count", "expires_at", "is_active")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code", "description")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__email", "product__product_name")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_verified_purchase", "is_approved", "created_at")
    list_filter = ("rating", "is_verified_purchase", "is_approved")
    search_fields = ("product__product_name", "user__email", "comment")
