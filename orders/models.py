"""Order models."""

from decimal import Decimal

from django.db import models

from accounts.models import Address, Customer
from catalog.models import ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        CONFIRMED = "confirmed", "Confirmed"
        PACKED = "packed", "Packed"
        SHIPPED = "shipped", "Shipped"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        COD = "cod", "Cash on Delivery"
        PREPAID = "prepaid", "Prepaid"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    customer = models.ForeignKey(
        Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )
    guest_name = models.CharField(max_length=120, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)

    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PLACED
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    shipping_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )

    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.COD
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    shipping_address = models.ForeignKey(
        Address, null=True, blank=True, on_delete=models.SET_NULL
    )
    shipping_name = models.CharField(max_length=120, blank=True)
    shipping_phone = models.CharField(max_length=20, blank=True)
    shipping_line1 = models.CharField(max_length=200, blank=True)
    shipping_line2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=80, blank=True)
    shipping_state = models.CharField(max_length=80, blank=True)
    shipping_pincode = models.CharField(max_length=10, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.order_number

    @property
    def display_name(self) -> str:
        if self.customer_id and self.customer.full_name:
            return self.customer.full_name
        return self.guest_name or self.shipping_name or "Guest"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        ProductVariant, null=True, on_delete=models.SET_NULL
    )
    product_name = models.CharField(max_length=200)
    size_code = models.CharField(max_length=10)
    colour_name = models.CharField(max_length=60)
    sku = models.CharField(max_length=64)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.product_name} x {self.qty}"
