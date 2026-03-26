from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from category.models import Category
from store.models import Product, Review, Variation, VariationCategory


class StoreViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(catergory_name="Shoes", slug="shoes")
        self.product = Product.objects.create(
            product_name="Runner",
            slug="runner",
            price="120.00",
            discount_price="95.00",
            stock=8,
            brand="Acme",
            category=self.category,
        )
        color, _ = VariationCategory.objects.get_or_create(name="color", defaults={"display_name": "Color"})
        size, _ = VariationCategory.objects.get_or_create(name="size", defaults={"display_name": "Size"})
        Variation.objects.create(product=self.product, variation_category=color, variation_value="red")
        Variation.objects.create(product=self.product, variation_category=size, variation_value="xl")

    def test_store_filters_by_brand_size_and_stock(self):
        response = self.client.get(
            reverse("store"),
            {"brand": "Acme", "size": "xl", "in_stock": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Runner")

    def test_product_detail_renders_reviews(self):
        user = Account.objects.create_user(
            first_name="Jane",
            last_name="Doe",
            username="jane",
            email="jane@example.com",
            password="secret123",
        )
        Review.objects.create(user=user, product=self.product, rating=4, comment="Solid shoe", is_verified_purchase=True)
        response = self.client.get(reverse("product_detail", args=[self.category.slug, self.product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solid shoe")
