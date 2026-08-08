"""Cart models."""

from django.conf import settings
from django.db import models

from catalog.models import ProductVariant


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="carts",
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["session_key"]),
        ]

    def __str__(self) -> str:
        owner = self.user.username if self.user_id else self.session_key
        return f"Cart({owner})"

    @property
    def item_count(self) -> int:
        return sum(item.qty for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.select_related("variant", "variant__product"))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "variant")

    def __str__(self) -> str:
        return f"{self.variant} x {self.qty}"

    @property
    def line_total(self):
        return self.variant.unit_price * self.qty
