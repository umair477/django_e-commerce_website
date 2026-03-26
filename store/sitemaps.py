from django.contrib.sitemaps import Sitemap

from category.models import Category
from store.models import Product


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True, category__is_active=True).select_related("category")

    def lastmod(self, obj):
        return obj.modified_date


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.filter(is_active=True)
