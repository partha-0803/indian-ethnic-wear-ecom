"""Template context for storefront chrome."""

from catalog.models import Category
from core.models import StoreSettings
from cart.services import get_cart_item_count


def storefront(request):
    settings = StoreSettings.load()
    return {
        "store": settings,
        "cart_count": get_cart_item_count(request),
        "store_categories": Category.objects.filter(is_active=True).order_by("sort_order")[:6],
    }
