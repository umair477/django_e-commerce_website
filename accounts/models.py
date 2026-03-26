from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email address")
        if not username:
            raise ValueError("User must have a username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, username, password, **extra_fields):
        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=password,
            **extra_fields,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_active = True
        user.is_superadmin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser, PermissionsMixin):
    LANGUAGE_CHOICES = (
        ("en", _("English")),
        ("it", _("Italian")),
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True, db_index=True)
    email = models.EmailField(max_length=100, unique=True, db_index=True)
    phone_number = models.CharField(max_length=50, blank=True)
    profile_image = models.ImageField(upload_to="accounts/profile-images/", blank=True, null=True)
    preferred_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="en")
    email_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = MyAccountManager()

    class Meta:
        ordering = ("-date_joined",)
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
        ]

    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_full_name(self):
        return self.full_name()

    def get_short_name(self):
        return self.first_name or self.username

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin or self.is_superuser

    def has_module_perms(self, app_label):
        return True


class Address(models.Model):
    BILLING = "billing"
    SHIPPING = "shipping"
    BOTH = "both"
    ADDRESS_TYPE_CHOICES = (
        (BILLING, _("Billing")),
        (SHIPPING, _("Shipping")),
        (BOTH, _("Billing & Shipping")),
    )

    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=50, blank=True, help_text=_("Home, Office, Warehouse, etc."))
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=50, blank=True)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default=BOTH)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_default", "-updated_at")
        indexes = [
            models.Index(fields=["user", "address_type"]),
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self):
        label = f" ({self.label})" if self.label else ""
        return f"{self.full_name}{label}"

    def full_address(self):
        parts = [self.address_line_1, self.address_line_2, self.city, self.state, self.country]
        return ", ".join(part for part in parts if part)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            (
                Address.objects.filter(user=self.user, address_type=self.address_type)
                .exclude(pk=self.pk)
                .update(is_default=False)
            )


class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    profile_picture = models.ImageField(blank=True, upload_to="userprofile")
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)

    def __str__(self):
        return self.user.first_name

    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2}".strip()
