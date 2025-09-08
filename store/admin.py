from django.contrib import admin
from . models import *
# Register your models here.

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_active', 'order')

class VariationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_active', 'created_date')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'created_date')
    search_fields = ('name', 'display_name')
    prepopulated_fields = {'name': ('display_name',)}
    autocomplete_fields = []

class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('product_name',)}
    list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
    search_fields = ('product_name', 'description')
    inlines = [ProductImageInline]

class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'alt_text', 'is_active', 'order', 'created_date')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active', 'created_date', 'product')
    search_fields = ('product__product_name', 'alt_text')
    autocomplete_fields = ['product']

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'is_active')
    search_fields = ('product__product_name', 'variation_value')
    autocomplete_fields = ['product', 'variation_category']


admin.site.register(VariationCategory, VariationCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Variation, VariationAdmin)