from django.test import TestCase
from django.urls import reverse

from accounts.models import Account, Address
from carts.models import CartItem
from category.models import Category
from orders.models import Order, OrderProduct
from store.models import Coupon, Product


class CheckoutFlowTests(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
            first_name="John",
            last_name="Shopper",
            username="john",
            email="john@example.com",
            password="secret123",
        )
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
        self.client.force_login(self.user)

        self.address = Address.objects.create(
            user=self.user,
            full_name="John Shopper",
            address_line_1="221B Baker Street",
            city="London",
            state="London",
            postal_code="NW1",
            country="UK",
            address_type=Address.BOTH,
            is_default=True,
        )
        self.category = Category.objects.create(catergory_name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            product_name="Headphones",
            slug="headphones",
            price="100.00",
            stock=10,
            category=self.category,
        )
        self.coupon = Coupon.objects.create(code="SAVE10", amount="10.00", usage_limit=5)

    def _checkout_payload(self, **overrides):
        payload = {
            "payment_method": "cod",
            "billing_address_id": self.address.id,
            "shipping_address_id": self.address.id,
            "same_as_billing": "on",
            "save_address": "on",
            "coupon_code": "SAVE10",
            "first_name": "John",
            "last_name": "Shopper",
            "phone": "123456",
            "email": "john@example.com",
            "address_line_1": "221B Baker Street",
            "address_line_2": "",
            "city": "London",
            "state": "London",
            "postal_code": "NW1",
            "country": "UK",
            "order_note": "Handle with care",
        }
        payload.update(overrides)
        return payload

    def test_place_order_with_cash_on_delivery(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=2)
        response = self.client.post(reverse("place_order"), self._checkout_payload())

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.user, is_ordered=True)
        self.product.refresh_from_db()
        self.coupon.refresh_from_db()

        self.assertEqual(order.payment_method, "cod")
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_UNPAID)
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(self.coupon.used_count, 1)
        self.assertEqual(OrderProduct.objects.filter(order=order).count(), 1)

    def test_place_order_with_easypaisa_marks_pending_verification(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.post(
            reverse("place_order"),
            self._checkout_payload(
                payment_method="easypaisa",
                coupon_code="",
                mobile_account_phone="03001234567",
                transaction_id="TXN-123",
                order_note="",
            ),
        )

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.user, is_ordered=True)
        self.assertEqual(order.payment_method, "easypaisa")
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_PENDING_VERIFICATION)
        self.assertEqual(order.transaction_id, "TXN-123")
        self.assertEqual(OrderProduct.objects.filter(order=order).count(), 1)

    def test_order_detail_is_available_to_owner_only(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        self.client.post(reverse("place_order"), self._checkout_payload())
        order = Order.objects.get(user=self.user, is_ordered=True)

        detail_response = self.client.get(reverse("order_detail", args=[order.id]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, order.order_number)
        self.assertContains(detail_response, "Order details")

        other_user = Account.objects.create_user(
            first_name="Other",
            last_name="User",
            username="other",
            email="other@example.com",
            password="secret123",
        )
        other_user.is_active = True
        other_user.save(update_fields=["is_active"])
        self.client.force_login(other_user)
        forbidden_response = self.client.get(reverse("order_detail", args=[order.id]))
        self.assertEqual(forbidden_response.status_code, 403)
