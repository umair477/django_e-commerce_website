from django.contrib import admin
from django.db.models import Avg, Sum
from django.template.response import TemplateResponse

from .models import Order, OrderProduct, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "user", "provider", "mobile_account_phone", "amount_payed", "status", "created_at")
    list_filter = ("provider", "status", "created_at")
    search_fields = ("payment_id", "transaction_id", "user__email")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/orders/order/change_list.html"
    list_display = ("order_number", "user", "payment_method", "payment_status", "status", "order_total", "created_at")
    list_filter = ("status", "payment_status", "payment_method", "created_at")
    search_fields = ("order_number", "email", "first_name", "last_name", "transaction_id")
    readonly_fields = ("order_number", "transaction_id", "subtotal", "discount_total", "order_total")

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            queryset = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response

        summary = queryset.aggregate(
            total_revenue=Sum("order_total"),
            average_order=Avg("order_total"),
        )
        response.context_data["sales_overview"] = {
            "total_orders": queryset.count(),
            "total_revenue": summary["total_revenue"] or 0,
            "average_order": summary["average_order"] or 0,
        }
        return response


@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "user", "quantity", "product_price", "ordered", "created_at")
    list_filter = ("ordered", "created_at")
    search_fields = ("order__order_number", "product__product_name", "user__email")
