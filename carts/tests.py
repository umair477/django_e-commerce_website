from django.test import TestCase
from django.urls import reverse

from category.models import Category
from store.models import Product


class CartAjaxTests(TestCase):
    def setUp(self):
        category = Category.objects.create(catergory_name="Accessories", slug="accessories")
        self.product = Product.objects.create(
            product_name="Belt",
            slug="belt",
            price="20.00",
            stock=5,
            category=category,
        )

    def test_ajax_add_to_cart_returns_json_and_creates_item(self):
        response = self.client.post(
            reverse("add_cart", args=[self.product.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "success": True,
                "product_name": "Belt",
                "product_price": "20.00",
                "quantity_added": 1,
                "cart_total_price": "20.00",
                "image_url": "",
                "cart_count": 1,
            },
        )

        cart_response = self.client.get(reverse("cart"))
        self.assertContains(cart_response, "Belt")
