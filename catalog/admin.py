from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Category, Colour, Product, ProductImage, ProductVariant, Size


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "is_primary", "alt", "sort_order")
    readonly_fields = ("preview",)

    @admin.display(description="Current")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" alt="" style="height:64px;width:48px;object-fit:cover;'
                'border:1px solid #ddd;" />',
                obj.image.url,
            )
        return "— new —"


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("size", "colour", "sku", "price_override", "stock_qty", "is_active")
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "description", "image")}),
        ("Visibility", {"fields": ("is_active", "sort_order")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
    )


@admin.register(Size)
class SizeAdmin(ModelAdmin):
    list_display = ("code", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("code",)


@admin.register(Colour)
class ColourAdmin(ModelAdmin):
    list_display = ("name", "hex", "sort_order")
    list_editable = ("hex", "sort_order")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = (
        "thumb",
        "name",
        "category",
        "base_price",
        "material",
        "made_in",
        "is_active",
        "is_featured",
        "updated_at",
    )
    list_display_links = ("thumb", "name")
    list_filter = ("category", "is_active", "is_featured", "made_in")
    search_fields = ("name", "slug", "description", "material")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active", "is_featured")
    filter_horizontal = ("related_products",)
    inlines = [ProductImageInline, ProductVariantInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "description",
                    "featured_image",
                ),
                "description": (
                    "Featured image is the main photo on shop cards and the product page. "
                    "Upload or replace it here to choose which image leads. "
                    "Add extra photos under Product images below — they appear as gallery "
                    "thumbnails only when more than one unique image exists."
                ),
            },
        ),
        (
            "Product details",
            {
                "fields": (
                    "material",
                    "made_in",
                    "fit",
                    "care_instructions",
                    "size_chart",
                    "details_extra",
                )
            },
        ),
        (
            "You may also like",
            {
                "fields": ("related_products",),
                "description": "Pick products to show in the related section. Leave empty to auto-fill from the same category.",
            },
        ),
        ("Pricing", {"fields": ("base_price", "hsn_code", "gst_rate")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
        ("Visibility", {"fields": ("is_active", "is_featured")}),
    )

    @admin.display(description="")
    def thumb(self, obj):
        img = obj.primary_image
        if img and getattr(img, "image", None):
            return format_html(
                '<img src="{}" style="height:40px;width:32px;object-fit:cover;" />',
                img.image.url,
            )
        return "—"


@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ("preview", "product", "is_primary", "sort_order", "alt")
    list_filter = ("is_primary", "product__category")
    list_editable = ("is_primary", "sort_order")
    search_fields = ("product__name", "alt")
    autocomplete_fields = ("product",)
    fields = ("product", "image", "is_primary", "alt", "sort_order", "preview")
    readonly_fields = ("preview",)

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-height:160px;max-width:120px;object-fit:cover;" />',
                obj.image.url,
            )
        return "—"


@admin.register(ProductVariant)
class ProductVariantAdmin(ModelAdmin):
    list_display = (
        "sku",
        "product",
        "size",
        "colour",
        "stock_qty",
        "price_override",
        "is_active",
    )
    list_filter = ("size", "colour", "is_active", "product__category")
    search_fields = ("sku", "product__name")
    list_editable = ("stock_qty", "is_active")
    autocomplete_fields = ("product",)
