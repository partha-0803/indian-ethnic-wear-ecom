"""Cart views with HTMX partials."""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from catalog.models import ProductVariant
from cart import services


def cart_detail(request):
    cart = services.get_or_create_cart(request)
    items = cart.items.select_related(
        "variant", "variant__product", "variant__size", "variant__colour"
    ).prefetch_related("variant__product__images")
    return render(
        request,
        "cart/cart.html",
        {"cart": cart, "items": items, "subtotal": cart.subtotal},
    )


@require_POST
def add_to_cart(request):
    variant_id = request.POST.get("variant_id")
    qty = int(request.POST.get("qty", 1) or 1)
    variant = get_object_or_404(ProductVariant, pk=variant_id, is_active=True)
    try:
        services.add_to_cart(request, variant, qty)
        messages.success(request, f"Added {variant.product.name} to cart")
    except ValueError as exc:
        messages.error(request, str(exc))
        if request.htmx:
            return HttpResponse(status=400)
        return redirect(variant.product.get_absolute_url())

    if request.htmx:
        return render(
            request,
            "partials/cart_badge.html",
            {"cart_count": services.get_cart_item_count(request)},
        )
    return redirect("cart:detail")


@require_http_methods(["POST"])
def update_item(request, item_id):
    qty = int(request.POST.get("qty", 1) or 0)
    cart = services.update_cart_item(request, item_id, qty)
    items = cart.items.select_related(
        "variant", "variant__product", "variant__size", "variant__colour"
    ).prefetch_related("variant__product__images")
    if request.htmx:
        return render(
            request,
            "cart/partials/cart_body.html",
            {
                "cart": cart,
                "items": items,
                "subtotal": cart.subtotal,
                "cart_count": services.get_cart_item_count(request),
            },
        )
    return redirect("cart:detail")


@require_POST
def remove_item(request, item_id):
    cart = services.remove_cart_item(request, item_id)
    items = cart.items.select_related(
        "variant", "variant__product", "variant__size", "variant__colour"
    ).prefetch_related("variant__product__images")
    if request.htmx:
        return render(
            request,
            "cart/partials/cart_body.html",
            {
                "cart": cart,
                "items": items,
                "subtotal": cart.subtotal,
                "cart_count": services.get_cart_item_count(request),
            },
        )
    return redirect("cart:detail")
