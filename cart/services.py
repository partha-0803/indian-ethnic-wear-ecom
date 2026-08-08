"""Cart services: get/merge cart, add/update/remove items."""

from __future__ import annotations

from django.db import transaction
from django.http import HttpRequest

from catalog.models import ProductVariant
from cart.models import Cart, CartItem


def _ensure_session(request: HttpRequest) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_or_create_cart(request: HttpRequest) -> Cart:
    """Return the active cart for the request (user or session)."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    session_key = _ensure_session(request)
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart


def get_cart_item_count(request: HttpRequest) -> int:
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            sk = request.session.session_key
            if not sk:
                return 0
            cart = Cart.objects.filter(session_key=sk, user=None).first()
        if not cart:
            return 0
        return cart.item_count
    except Exception:
        return 0


@transaction.atomic
def merge_session_cart_to_user(request: HttpRequest) -> None:
    """Merge anonymous session cart into the logged-in user's cart."""
    if not request.user.is_authenticated:
        return
    sk = request.session.session_key
    if not sk:
        return
    session_cart = Cart.objects.filter(session_key=sk, user=None).first()
    if not session_cart:
        return
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    for item in session_cart.items.select_related("variant"):
        existing = user_cart.items.filter(variant=item.variant).first()
        if existing:
            existing.qty = min(existing.qty + item.qty, item.variant.stock_qty or existing.qty)
            existing.save(update_fields=["qty"])
        else:
            item.cart = user_cart
            item.save(update_fields=["cart"])
    session_cart.delete()


def add_to_cart(request: HttpRequest, variant: ProductVariant, qty: int = 1) -> CartItem:
    if qty < 1:
        raise ValueError("Quantity must be at least 1")
    if not variant.in_stock:
        raise ValueError("This variant is out of stock")
    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(
        cart=cart, variant=variant, defaults={"qty": min(qty, variant.stock_qty)}
    )
    if not created:
        item.qty = min(item.qty + qty, variant.stock_qty)
        item.save(update_fields=["qty"])
    return item


def update_cart_item(request: HttpRequest, item_id: int, qty: int) -> Cart | None:
    cart = get_or_create_cart(request)
    item = cart.items.filter(pk=item_id).select_related("variant").first()
    if not item:
        return cart
    if qty <= 0:
        item.delete()
    else:
        item.qty = min(qty, item.variant.stock_qty)
        item.save(update_fields=["qty"])
    return cart


def remove_cart_item(request: HttpRequest, item_id: int) -> Cart:
    cart = get_or_create_cart(request)
    cart.items.filter(pk=item_id).delete()
    return cart
