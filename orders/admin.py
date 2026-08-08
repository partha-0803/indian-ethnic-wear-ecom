from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product_name",
        "size_code",
        "colour_name",
        "sku",
        "qty",
        "unit_price",
        "tax_rate",
        "tax_amount",
        "line_total",
    )


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "order_number",
        "display_name",
        "status",
        "payment_method",
        "payment_status",
        "grand_total",
        "created_at",
    )
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = (
        "order_number",
        "guest_name",
        "guest_email",
        "guest_phone",
        "shipping_pincode",
    )
    list_editable = ("status", "payment_status")
    readonly_fields = (
        "order_number",
        "subtotal",
        "tax_total",
        "shipping_total",
        "grand_total",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order_number",
                    "customer",
                    "status",
                    "payment_method",
                    "payment_status",
                )
            },
        ),
        (
            "Guest / Contact",
            {"fields": ("guest_name", "guest_email", "guest_phone")},
        ),
        (
            "Shipping snapshot",
            {
                "fields": (
                    "shipping_name",
                    "shipping_phone",
                    "shipping_line1",
                    "shipping_line2",
                    "shipping_city",
                    "shipping_state",
                    "shipping_pincode",
                )
            },
        ),
        (
            "Totals",
            {"fields": ("subtotal", "tax_total", "shipping_total", "grand_total", "notes")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
