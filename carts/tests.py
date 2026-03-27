from django.test import TestCase
from django.urls import reverse

from carts.models import CartItem
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

    def test_ajax_add_to_cart_returns_json_and_respects_quantity(self):
        response = self.client.post(
            reverse("add_cart", args=[self.product.id]),
            {"quantity": 3},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "success": True,
                "product_name": "Belt",
                "product_price": "20.00",
                "quantity_added": 3,
                "cart_total_price": "60.00",
                "image_url": "",
                "cart_count": 3,
                "tax": "1.20",
                "shipping": "0.00",
                "grand_total": "61.20",
                "message": "Cart updated successfully.",
            },
        )

        cart_response = self.client.get(reverse("cart"))
        self.assertContains(cart_response, "Belt")

    def test_update_cart_item_returns_backend_totals(self):
        self.client.post(reverse("add_cart", args=[self.product.id]), {"quantity": 1})
        cart_item = CartItem.objects.get(product=self.product)

        response = self.client.post(
            reverse("update_cart_item", args=[cart_item.id]),
            {"action": "increment"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "success": True,
                "message": "Cart updated successfully.",
                "item_removed": False,
                "cart_empty": False,
                "cart_count": 2,
                "cart_total": "40.00",
                "tax": "0.80",
                "shipping": "0.00",
                "grand_total": "40.80",
                "item_id": cart_item.id,
                "quantity": 2,
                "item_subtotal": "40.00",
                "product_price": "20.00",
                "max_quantity": 5,
            },
        )
