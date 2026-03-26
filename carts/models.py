from django.db import models

from accounts.models import Account
from store.models import Product, Variation


class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True, db_index=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id


class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    variations = models.ManyToManyField(Variation, blank=True, related_name="cart_items")
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True, related_name="items")
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("id",)

    def sub_total(self):
        return self.product.effective_price * self.quantity

    def __str__(self):
        return self.product.product_name
