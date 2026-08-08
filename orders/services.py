"""Order placement services (COD / pay-later)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from accounts.models import Address, Customer
from cart.models import Cart
from core.models import StoreSettings
from orders.models import Order, OrderItem


def generate_order_number() -> str:
    stamp = timezone.now().strftime("%y%m%d")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"DV-{stamp}-{suffix}"


def compute_shipping(subtotal: Decimal, settings: StoreSettings) -> Decimal:
    if subtotal >= settings.free_shipping_over:
        return Decimal("0.00")
    return settings.flat_shipping_rate


@transaction.atomic
def place_cod_order(
    *,
    cart: Cart,
    customer: Customer | None,
    address_data: dict,
    guest_email: str = "",
    guest_phone: str = "",
    guest_name: str = "",
    notes: str = "",
) -> Order:
    """Create a COD order from cart, snapshot prices, decrement stock."""
    items = list(cart.items.select_related("variant", "variant__product", "variant__size", "variant__colour"))
    if not items:
        raise ValueError("Cart is empty")

    for item in items:
        if item.qty > item.variant.stock_qty:
            raise ValueError(f"Insufficient stock for {item.variant}")

    settings = StoreSettings.load()
    subtotal = sum((item.variant.unit_price * item.qty for item in items), Decimal("0"))
    shipping = compute_shipping(subtotal, settings)
    tax_total = Decimal("0.00")
    if settings.gst_enabled:
        rate = settings.default_gst_rate
        tax_total = (subtotal * rate / Decimal("100")).quantize(Decimal("0.01"))
    grand = subtotal + tax_total + shipping

    address = None
    if customer:
        address = Address.objects.create(
            customer=customer,
            full_name=address_data["full_name"],
            phone=address_data["phone"],
            line1=address_data["line1"],
            line2=address_data.get("line2", ""),
            city=address_data["city"],
            state=address_data["state"],
            pincode=address_data["pincode"],
            is_default=not customer.addresses.exists(),
        )

    order = Order.objects.create(
        order_number=generate_order_number(),
        customer=customer,
        guest_name=guest_name or address_data["full_name"],
        guest_email=guest_email or (customer.email if customer else ""),
        guest_phone=guest_phone or address_data["phone"],
        status=Order.Status.PLACED,
        subtotal=subtotal,
        tax_total=tax_total,
        shipping_total=shipping,
        grand_total=grand,
        payment_method=Order.PaymentMethod.COD,
        payment_status=Order.PaymentStatus.PENDING,
        shipping_address=address,
        shipping_name=address_data["full_name"],
        shipping_phone=address_data["phone"],
        shipping_line1=address_data["line1"],
        shipping_line2=address_data.get("line2", ""),
        shipping_city=address_data["city"],
        shipping_state=address_data["state"],
        shipping_pincode=address_data["pincode"],
        notes=notes,
    )

    for item in items:
        variant = item.variant
        unit = variant.unit_price
        line = unit * item.qty
        tax_rate = Decimal("0")
        tax_amount = Decimal("0")
        if settings.gst_enabled:
            tax_rate = settings.default_gst_rate
            tax_amount = (line * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        OrderItem.objects.create(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            size_code=variant.size.code,
            colour_name=variant.colour.name,
            sku=variant.sku,
            qty=item.qty,
            unit_price=unit,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            line_total=line,
        )
        variant.stock_qty = max(0, variant.stock_qty - item.qty)
        variant.save(update_fields=["stock_qty"])

    cart.items.all().delete()
    return order
