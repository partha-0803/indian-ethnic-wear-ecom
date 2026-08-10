"""Catalog models: categories, products, variants, sizes, colours."""

from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, max_length=140)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="categories/", blank=True, null=True, max_length=500
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:category", kwargs={"slug": self.slug})


class Size(models.Model):
    code = models.CharField(max_length=10, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "code"]

    def __str__(self) -> str:
        return self.code


class Colour(models.Model):
    name = models.CharField(max_length=60, unique=True)
    hex = models.CharField(max_length=7, default="#000000")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    hsn_code = models.CharField(max_length=20, blank=True)
    gst_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    featured_image = models.ImageField(
        upload_to="products/featured/",
        blank=True,
        null=True,
        max_length=500,
        help_text="Main image on shop cards & product page. Upload or replace here from the CMS.",
    )
    # Product details (CMS-editable)
    material = models.CharField(max_length=200, blank=True)
    made_in = models.CharField(max_length=120, blank=True, default="India")
    fit = models.CharField(max_length=120, blank=True)
    care_instructions = models.TextField(
        blank=True, help_text="How to wash / care for this garment"
    )
    size_chart = models.TextField(
        blank=True,
        help_text="Product-specific size chart. Leave blank to use the store default.",
    )
    details_extra = models.TextField(
        blank=True, help_text="Any other product information shown on the PDP"
    )
    related_products = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="related_from",
        help_text="Manual 'You may also like' picks. If empty, same-category products are shown.",
    )
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def primary_image(self):
        """Main storefront image: featured_image first, then marked primary gallery image."""
        if self.featured_image:
            return _FeaturedImageProxy(self.featured_image, self.name)
        marked = self.images.filter(is_primary=True).order_by("sort_order", "id").first()
        if marked:
            return marked
        return self.images.order_by("sort_order", "id").first()

    def gallery_images(self):
        """Images for PDP thumbs — featured first, then gallery (skipping duplicate primary)."""
        items = []
        if self.featured_image:
            items.append(_FeaturedImageProxy(self.featured_image, self.name))
        for img in self.images.all():
            items.append(img)
        return items

    def seo_title(self) -> str:
        return self.meta_title or f"{self.name} | DESI VIBES"

    def seo_description(self) -> str:
        if self.meta_description:
            return self.meta_description
        base = self.description or f"Shop {self.name} — modern ethnic wear for men."
        return base[:157] + ("…" if len(base) > 157 else "")

    def effective_size_chart(self) -> str:
        if self.size_chart.strip():
            return self.size_chart
        from core.models import StoreSettings

        return StoreSettings.load().default_size_chart

    def min_price(self) -> Decimal:
        overrides = [
            v.price_override
            for v in self.variants.filter(is_active=True)
            if v.price_override is not None
        ]
        if overrides:
            return min(min(overrides), self.base_price)
        return self.base_price


class _FeaturedImageProxy:
    """Duck-types ProductImage so templates can use .image.url and .alt."""

    def __init__(self, image, alt: str = ""):
        self.image = image
        self.alt = alt or ""


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/", max_length=500)
    alt = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Use as main image when Featured image above is empty.",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-is_primary", "sort_order", "id"]

    def __str__(self) -> str:
        tag = " (main)" if self.is_primary else ""
        return f"{self.product.name} image {self.sort_order}{tag}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            (
                ProductImage.objects.filter(product_id=self.product_id, is_primary=True)
                .exclude(pk=self.pk)
                .update(is_primary=False)
            )
            # Point product featured_image at this file (same storage path)
            Product.objects.filter(pk=self.product_id).update(
                featured_image=self.image.name
            )

class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    size = models.ForeignKey(Size, on_delete=models.PROTECT)
    colour = models.ForeignKey(Colour, on_delete=models.PROTECT)
    sku = models.CharField(max_length=64, unique=True)
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    stock_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("product", "size", "colour")
        ordering = ["size__sort_order", "colour__sort_order"]

    def __str__(self) -> str:
        return f"{self.product.name} / {self.size.code} / {self.colour.name}"

    @property
    def unit_price(self) -> Decimal:
        return self.price_override if self.price_override is not None else self.product.base_price

    @property
    def in_stock(self) -> bool:
        return self.is_active and self.stock_qty > 0
