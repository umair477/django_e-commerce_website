from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("catergory_name",)}
    list_display = ("catergory_name", "parent", "slug", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("catergory_name", "description")
