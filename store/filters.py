from django import forms
from django.db.models import Q

from .models import Product


try:
    import django_filters  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    django_filters = None


class ProductFilterForm(forms.Form):
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    brand = forms.CharField(required=False)
    size = forms.CharField(required=False)
    color = forms.CharField(required=False)
    in_stock = forms.BooleanField(required=False)


def _apply_product_filters(queryset, data):
    form = ProductFilterForm(data)
    if not form.is_valid():
        return queryset, form

    cleaned = form.cleaned_data
    if cleaned.get("min_price") is not None:
        queryset = queryset.filter(Q(price__gte=cleaned["min_price"]) | Q(discount_price__gte=cleaned["min_price"]))
    if cleaned.get("max_price") is not None:
        queryset = queryset.filter(Q(discount_price__lte=cleaned["max_price"]) | Q(price__lte=cleaned["max_price"]))
    if cleaned.get("brand"):
        queryset = queryset.filter(brand__iexact=cleaned["brand"])
    if cleaned.get("size"):
        queryset = queryset.filter(
            variations__variation_category__name__iexact="size",
            variations__variation_value__iexact=cleaned["size"],
        )
    if cleaned.get("color"):
        queryset = queryset.filter(
            variations__variation_category__name__iexact="color",
            variations__variation_value__iexact=cleaned["color"],
        )
    if cleaned.get("in_stock"):
        queryset = queryset.filter(stock__gt=0)
    return queryset.distinct(), form


if django_filters:
    class ProductFilter(django_filters.FilterSet):
        min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
        max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
        brand = django_filters.CharFilter(field_name="brand", lookup_expr="iexact")
        in_stock = django_filters.BooleanFilter(method="filter_in_stock")
        size = django_filters.CharFilter(method="filter_size")
        color = django_filters.CharFilter(method="filter_color")

        class Meta:
            model = Product
            fields = ["min_price", "max_price", "brand", "size", "color", "in_stock"]

        def filter_in_stock(self, queryset, name, value):
            return queryset.filter(stock__gt=0) if value else queryset

        def filter_size(self, queryset, name, value):
            return queryset.filter(
                variations__variation_category__name__iexact="size",
                variations__variation_value__iexact=value,
            )

        def filter_color(self, queryset, name, value):
            return queryset.filter(
                variations__variation_category__name__iexact="color",
                variations__variation_value__iexact=value,
            )

    def build_product_filter(queryset, data):
        filterset = ProductFilter(data, queryset=queryset)
        return filterset.qs.distinct(), ProductFilterForm(data)
else:
    def build_product_filter(queryset, data):
        return _apply_product_filters(queryset, data)
