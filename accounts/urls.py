from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("orders/", views.account_orders, name="account_orders"),
    path("addresses/", views.account_addresses, name="account_addresses"),
    path("profile/", views.account_profile, name="account_profile"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path(
        "forgotPassword/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/forgotPassword.html",
            email_template_name="accounts/reset_password_email.html",
            subject_template_name="accounts/reset_password_subject.txt",
        ),
        name="forgotPassword",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("addresses/<int:address_id>/delete/", views.delete_address, name="delete_address"),
]
