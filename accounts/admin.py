from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Account, Address, UserProfile


@admin.register(Account)
class AccountAdmin(UserAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "preferred_language",
        "email_verified",
        "is_active",
        "date_joined",
    )
    list_display_links = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")
    ordering = ("-date_joined",)
    search_fields = ("email", "first_name", "last_name", "username")
    list_filter = ("preferred_language", "is_active", "is_staff", "email_verified")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "username", "phone_number", "profile_image", "preferred_language")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_admin", "is_superadmin", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "address_type", "city", "country", "is_default", "is_active")
    list_filter = ("address_type", "is_default", "is_active", "country")
    search_fields = ("full_name", "user__email", "city", "country", "label")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "state", "country")
