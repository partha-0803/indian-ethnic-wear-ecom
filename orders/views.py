"""Checkout and order views."""

import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.models import Customer
from cart import services as cart_services
from core.models import StoreSettings
from orders.models import Order
from orders.services import compute_shipping, place_cod_order


PHONE_RE = re.compile(r"^[6-9]\d{9}$")
PINCODE_RE = re.compile(r"^\d{6}$")


def _get_customer(user) -> Customer:
    customer, _ = Customer.objects.get_or_create(
        user=user,
        defaults={
            "email": user.email,
            "full_name": user.get_full_name() or user.username,
        },
    )
    return customer


@login_required
@require_http_methods(["GET", "POST"])
def checkout(request):
    cart = cart_services.get_or_create_cart(request)
    items = list(
        cart.items.select_related(
            "variant", "variant__product", "variant__size", "variant__colour"
        ).prefetch_related("variant__product__images")
    )
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:detail")

    settings = StoreSettings.load()
    subtotal = cart.subtotal
    shipping = compute_shipping(subtotal, settings)
    tax_total = 0
    grand = subtotal + shipping

    customer = _get_customer(request.user)
    errors = {}

    if request.method == "POST":
        data = {
            "full_name": request.POST.get("full_name", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "line1": request.POST.get("line1", "").strip(),
            "line2": request.POST.get("line2", "").strip(),
            "city": request.POST.get("city", "").strip(),
            "state": request.POST.get("state", "").strip(),
            "pincode": request.POST.get("pincode", "").strip(),
        }
        notes = request.POST.get("notes", "").strip()

        if not data["full_name"]:
            errors["full_name"] = "Name is required"
        if not PHONE_RE.match(data["phone"]):
            errors["phone"] = "Enter a valid 10-digit Indian mobile number"
        if not data["line1"]:
            errors["line1"] = "Address is required"
        if not data["city"]:
            errors["city"] = "City is required"
        if not data["state"]:
            errors["state"] = "State is required"
        if not PINCODE_RE.match(data["pincode"]):
            errors["pincode"] = "Enter a valid 6-digit pincode"

        if not errors:
            try:
                order = place_cod_order(
                    cart=cart,
                    customer=customer,
                    address_data=data,
                    guest_email=customer.email or request.user.email,
                    guest_phone=data["phone"],
                    guest_name=data["full_name"],
                    notes=notes,
                )
                messages.success(
                    request, f"Order {order.order_number} placed successfully!"
                )
                return redirect("orders:confirmation", order_number=order.order_number)
            except ValueError as exc:
                messages.error(request, str(exc))

        form_data = data
    else:
        form_data = {
            "full_name": customer.full_name or request.user.get_full_name(),
            "phone": customer.phone,
            "line1": "",
            "line2": "",
            "city": "",
            "state": "",
            "pincode": "",
        }
        default_addr = customer.addresses.filter(is_default=True).first()
        if default_addr:
            form_data.update(
                {
                    "full_name": default_addr.full_name,
                    "phone": default_addr.phone,
                    "line1": default_addr.line1,
                    "line2": default_addr.line2,
                    "city": default_addr.city,
                    "state": default_addr.state,
                    "pincode": default_addr.pincode,
                }
            )

    return render(
        request,
        "orders/checkout.html",
        {
            "items": items,
            "subtotal": subtotal,
            "shipping": shipping,
            "tax_total": tax_total,
            "grand_total": grand,
            "form_data": form_data,
            "errors": errors,
            "settings": settings,
        },
    )


@login_required
def confirmation(request, order_number):
    customer = _get_customer(request.user)
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        order_number=order_number,
        customer=customer,
    )
    return render(request, "orders/confirmation.html", {"order": order})


@login_required
def order_list(request):
    customer = _get_customer(request.user)
    orders = Order.objects.filter(customer=customer).prefetch_related("items")
    return render(request, "orders/list.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    customer = _get_customer(request.user)
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        order_number=order_number,
        customer=customer,
    )
    return render(request, "orders/detail.html", {"order": order})
