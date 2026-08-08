from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import CustomerReview, HeroSlide, StoreSettings


class HeroSlideAdmin(ModelAdmin):
    list_display = ("title", "sort_order", "is_active", "cta_label")
    list_editable = ("sort_order", "is_active")
    search_fields = ("title", "subtitle")


class CustomerReviewAdmin(ModelAdmin):
    list_display = (
        "customer_name",
        "rating",
        "location",
        "is_featured",
        "sort_order",
        "product",
    )
    list_editable = ("is_featured", "sort_order", "rating")
    list_filter = ("is_featured", "rating")
    search_fields = ("customer_name", "quote", "location")
    autocomplete_fields = ("product",)


@admin.register(StoreSettings)
class StoreSettingsAdmin(ModelAdmin):
    fieldsets = (
        (
            "Branding",
            {"fields": ("store_name", "tagline", "logo", "theme_color", "currency")},
        ),
        (
            "SEO",
            {"fields": ("meta_title", "meta_description", "seo_keywords")},
        ),
        (
            "Homepage — About Us",
            {"fields": ("about_title", "about_body", "about_image")},
        ),
        (
            "Homepage — Craft / Made In",
            {
                "fields": (
                    "craft_title",
                    "craft_body",
                    "craft_image",
                    "craft_locations",
                )
            },
        ),
        (
            "Default Size Chart",
            {
                "fields": ("default_size_chart",),
                "description": "Used on products that do not have their own size chart. Pipe-separated table rows work best.",
            },
        ),
        (
            "Contact",
            {"fields": ("support_email", "support_phone")},
        ),
        (
            "Payments",
            {"fields": ("cod_enabled", "prepaid_enabled")},
        ),
        (
            "Shipping",
            {"fields": ("free_shipping_over", "flat_shipping_rate", "shiprocket_enabled")},
        ),
        (
            "GST",
            {
                "fields": (
                    "gst_enabled",
                    "gstin",
                    "default_gst_rate",
                    "default_hsn",
                )
            },
        ),
        ("CRM", {"fields": ("crm_provider",)}),
    )

    def has_add_permission(self, request):
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(HeroSlide, HeroSlideAdmin)
admin.site.register(CustomerReview, CustomerReviewAdmin)
