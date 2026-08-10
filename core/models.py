"""Core store settings, homepage content, hero slides, reviews."""

from django.core.cache import cache
from django.db import models


DEFAULT_SIZE_CHART = """Size | Chest (in) | Waist (in) | Shoulder (in) | Length (in)
XS | 36 | 30 | 15.5 | 38
S | 38 | 32 | 16.5 | 40
M | 40 | 34 | 17.5 | 42
L | 42 | 36 | 18.5 | 44
XL | 44 | 38 | 19.5 | 46
XXL | 46 | 40 | 20.5 | 48

Tip: If you are between sizes, choose the larger size for a relaxed festive fit."""


class StoreSettings(models.Model):
    """Singleton config for branding, homepage copy, and feature toggles."""

    store_name = models.CharField(max_length=120, default="DESI VIBES")
    tagline = models.CharField(
        max_length=200, default="Modern Ethnic Wear for Men", blank=True
    )
    logo = models.ImageField(
        upload_to="brand/", blank=True, null=True, max_length=500
    )
    theme_color = models.CharField(max_length=20, default="#801C2A")
    currency = models.CharField(max_length=8, default="INR")

    # SEO / discoverability
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    seo_keywords = models.CharField(
        max_length=255,
        blank=True,
        default="ethnic wear, sherwani, kurta, bandhgala, nehru jacket, mens ethnic",
    )

    # Homepage — About
    about_title = models.CharField(max_length=120, blank=True, default="Our Story")
    about_body = models.TextField(
        blank=True,
        default=(
            "DESI VIBES was born from a love of Indian craft and modern silhouette. "
            "We design ethnic wear for men who want tradition with a contemporary edge—"
            "sharper cuts, richer fabrics, and colours that feel royal without the noise."
        ),
    )
    about_image = models.ImageField(
        upload_to="brand/", blank=True, null=True, max_length=500
    )

    # Homepage — Craft / Made in
    craft_title = models.CharField(
        max_length=120, blank=True, default="Crafted in India"
    )
    craft_body = models.TextField(
        blank=True,
        default=(
            "Every piece is cut and finished in India by skilled artisans. "
            "From Banarasi-inspired weaves to contemporary bandhgalas, our ateliers "
            "in Rajasthan and Uttar Pradesh bring heritage techniques into wearable luxury."
        ),
    )
    craft_image = models.ImageField(
        upload_to="brand/", blank=True, null=True, max_length=500
    )
    craft_locations = models.CharField(
        max_length=255,
        blank=True,
        default="Jaipur · Varanasi · New Delhi",
        help_text="Short line shown under craftsmanship section",
    )

    # Default size chart for products without their own
    default_size_chart = models.TextField(blank=True, default=DEFAULT_SIZE_CHART)

    gst_enabled = models.BooleanField(default=False)
    gstin = models.CharField(max_length=20, blank=True)
    default_gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    default_hsn = models.CharField(max_length=20, blank=True)

    cod_enabled = models.BooleanField(default=True)
    prepaid_enabled = models.BooleanField(default=False)

    crm_provider = models.CharField(
        max_length=20,
        choices=[("none", "None / Excel"), ("zoho", "Zoho CRM")],
        default="none",
    )
    shiprocket_enabled = models.BooleanField(default=False)

    free_shipping_over = models.DecimalField(
        max_digits=10, decimal_places=2, default=2999
    )
    flat_shipping_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=99
    )

    support_email = models.EmailField(default="hello@desivibes.demo")
    support_phone = models.CharField(max_length=20, default="+91 98765 43210")

    class Meta:
        verbose_name = "Store settings"
        verbose_name_plural = "Store settings"

    def __str__(self) -> str:
        return self.store_name

    def save(self, *args, **kwargs):
        self.pk = 1
        if not self.default_size_chart.strip():
            self.default_size_chart = DEFAULT_SIZE_CHART
        super().save(*args, **kwargs)
        cache.delete("store_settings")

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls) -> "StoreSettings":
        settings_obj = cache.get("store_settings")
        if settings_obj is None:
            settings_obj, _ = cls.objects.get_or_create(pk=1)
            cache.set("store_settings", settings_obj, 60)
        return settings_obj

    def seo_title(self) -> str:
        return self.meta_title or f"{self.store_name} — {self.tagline}"

    def seo_description(self) -> str:
        return self.meta_description or (
            f"{self.tagline}. Shop premium sherwanis, kurtas, bandhgalas and Nehru jackets "
            f"for men. Crafted in India."
        )[:160]


class HeroSlide(models.Model):
    """Homepage hero slideshow — editable in CMS."""

    title = models.CharField(max_length=120, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="hero/", max_length=500)
    mobile_image = models.ImageField(
        upload_to="hero/", blank=True, null=True, max_length=500
    )
    cta_label = models.CharField(max_length=60, blank=True, default="Shop Collection")
    cta_url = models.CharField(max_length=200, blank=True, default="/shop/")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.title or f"Slide {self.pk}"


class CustomerReview(models.Model):
    """Homepage / social-proof reviews — editable in CMS."""

    customer_name = models.CharField(max_length=120)
    location = models.CharField(max_length=120, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    quote = models.TextField()
    product = models.ForeignKey(
        "catalog.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews",
    )
    is_featured = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self) -> str:
        return f"{self.customer_name} ({self.rating}★)"
