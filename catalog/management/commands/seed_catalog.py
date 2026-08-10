"""
Seed DESI VIBES demo catalog: categories, 5 products each, variants, images, users.

Usage:
    python manage.py seed_catalog
    python manage.py seed_catalog --reset
"""

from __future__ import annotations

import io
import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from accounts.models import Customer
from catalog.models import Category, Colour, Product, ProductImage, ProductVariant, Size
from core.models import StoreSettings

CATEGORIES = [
    {
        "name": "Kurtas",
        "slug": "kurtas",
        "description": "Contemporary kurtas for festivities and everyday elegance.",
        "sort_order": 1,
        "price_range": (1499, 4999),
        "prefixes": [
            "Royal",
            "Heritage",
            "Luxe",
            "Nawab",
            "Festival",
            "Midnight",
            "Ivory",
            "Ember",
            "Silk",
            "Cotton",
            "Bandhani",
            "Chanderi",
            "Banarasi",
            "Jaipur",
            "Rajasthani",
        ],
        "suffixes": [
            "Kurta",
            "Straight Kurta",
            "Pathani Kurta",
            "Asymmetric Kurta",
            "Collar Kurta",
            "Embroidered Kurta",
            "Printed Kurta",
            "Linen Kurta",
        ],
    },
    {
        "name": "Sherwanis",
        "slug": "sherwanis",
        "description": "Statement sherwanis crafted for weddings and grand occasions.",
        "sort_order": 2,
        "price_range": (8999, 34999),
        "prefixes": [
            "Imperial",
            "Regal",
            "Maharaja",
            "Velvet",
            "Goldwork",
            "Pearl",
            "Ceremonial",
            "Wedding",
            "Grand",
            "Classic",
            "Opulent",
            "Heritage",
            "Royal",
            "Bespoke",
            "Legacy",
        ],
        "suffixes": [
            "Sherwani",
            "Achkan Sherwani",
            "Indo Sherwani",
            "Embroidered Sherwani",
            "Velvet Sherwani",
            "Bridal Party Sherwani",
        ],
    },
    {
        "name": "Indo-Western",
        "slug": "indo-western",
        "description": "Bandhgalas and fusion silhouettes with a modern cut.",
        "sort_order": 3,
        "price_range": (3999, 15999),
        "prefixes": [
            "Urban",
            "Noir",
            "Gatsby",
            "Metro",
            "Fusion",
            "Tailored",
            "Sleek",
            "Modern",
            "Studio",
            "Evening",
            "Cocktail",
            "Structured",
            "Minimal",
            "Bold",
            "Prime",
        ],
        "suffixes": [
            "Bandhgala",
            "Indo Suit",
            "Jodhpuri",
            "Waistcoat Set",
            "Fusion Blazer",
            "Nehru Suit",
        ],
    },
    {
        "name": "Nehru Jackets",
        "slug": "nehru-jackets",
        "description": "Layer-ready Nehru jackets in rich textures and tones.",
        "sort_order": 4,
        "price_range": (1999, 7999),
        "prefixes": [
            "Classic",
            "Textured",
            "Brocade",
            "Linen",
            "Quilted",
            "Festive",
            "Midnight",
            "Suede",
            "Jacquard",
            "Printed",
            "Silk",
            "Cotton",
            "Embellished",
            "Slim",
            "Grand",
        ],
        "suffixes": [
            "Nehru Jacket",
            "Modi Jacket",
            "Waistcoat",
            "Collar Jacket",
            "Brocade Jacket",
        ],
    },
]

SIZES = [("XS", 1), ("S", 2), ("M", 3), ("L", 4), ("XL", 5), ("XXL", 6)]

COLOURS = [
    ("Gold", "#C9A227", 1),
    ("Maroon", "#801C2A", 2),
    ("Ivory", "#F5F0E6", 3),
    ("Navy", "#1B2A4A", 4),
    ("Black", "#1A1210", 5),
    ("Emerald", "#0F5C4C", 6),
]

PRODUCTS_PER_CATEGORY = 5
COLOURS_PER_PRODUCT = 4

# Hex backgrounds for generated product imagery
PALETTES = [
    ((128, 28, 42), (201, 162, 39)),
    ((26, 18, 16), (128, 28, 42)),
    ((27, 42, 74), (201, 162, 39)),
    ((15, 92, 76), (245, 240, 230)),
    ((139, 105, 20), (26, 18, 16)),
    ((90, 16, 28), (228, 200, 106)),
]


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _load_font(size: int):
    for name in (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        path = Path(name)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def generate_product_image(
    title: str, colour_hex: str, width: int = 800, height: int = 1067
) -> ContentFile:
    """Create a royal-styled product image with Pillow."""
    base = _hex_to_rgb(colour_hex)
    accent = random.choice(PALETTES)[1]
    img = Image.new("RGB", (width, height), base)
    draw = ImageDraw.Draw(img)

    # Soft gradient overlay via bands
    for y in range(height):
        ratio = y / height
        r = int(base[0] * (1 - ratio) + accent[0] * ratio * 0.35)
        g = int(base[1] * (1 - ratio) + accent[1] * ratio * 0.35)
        b = int(base[2] * (1 - ratio) + accent[2] * ratio * 0.35)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Decorative frame
    margin = 36
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline=(201, 162, 39),
        width=3,
    )
    draw.rectangle(
        [margin + 10, margin + 10, width - margin - 10, height - margin - 10],
        outline=(245, 240, 230),
        width=1,
    )

    # Abstract garment silhouette (simplified kurta shape)
    cx, top = width // 2, int(height * 0.22)
    body_w, body_h = int(width * 0.42), int(height * 0.48)
    fill = (245, 240, 230) if sum(base) < 380 else (26, 18, 16)
    draw.rounded_rectangle(
        [cx - body_w // 2, top, cx + body_w // 2, top + body_h],
        radius=18,
        fill=fill,
        outline=(201, 162, 39),
        width=2,
    )
    # Collar
    draw.polygon(
        [
            (cx - 40, top),
            (cx, top + 28),
            (cx + 40, top),
        ],
        fill=base,
    )
    # Buttons
    for i in range(5):
        by = top + 70 + i * 55
        draw.ellipse([cx - 5, by, cx + 5, by + 10], fill=(201, 162, 39))

    font_sm = _load_font(22)
    font_lg = _load_font(36)
    brand = "DESI VIBES"
    draw.text(
        (width // 2, height - 120),
        brand,
        fill=(201, 162, 39),
        font=font_sm,
        anchor="mm",
    )
    # Wrap title
    words = title.split()
    lines = []
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        if len(test) > 22:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    y = height - 90
    for ln in lines[:2]:
        draw.text((width // 2, y), ln, fill=(245, 240, 230), font=font_lg, anchor="mm")
        y += 40

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=85, method=4)
    return ContentFile(
        buf.getvalue(), name=f"{title[:40].replace(' ', '-').lower()}.webp"
    )


def generate_logo() -> ContentFile:
    img = Image.new("RGB", (512, 512), (247, 241, 232))
    draw = ImageDraw.Draw(img)
    # Split garment icon
    draw.rounded_rectangle([156, 80, 256, 320], radius=8, fill=(201, 162, 39))
    draw.rounded_rectangle([256, 80, 356, 320], radius=8, fill=(128, 28, 42))
    draw.rectangle([156, 80, 356, 110], fill=(26, 18, 16))
    for i in range(5):
        y = 130 + i * 30
        draw.ellipse([268, y, 280, y + 12], fill=(26, 18, 16))
    draw.polygon([(300, 140), (330, 140), (315, 165)], fill=(201, 162, 39))
    font = _load_font(36)
    draw.text((256, 380), "DESI VIBES", fill=(26, 18, 16), font=font, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=90, method=4)
    return ContentFile(buf.getvalue(), name="logo.webp")


def generate_hero() -> ContentFile:
    img = Image.new("RGB", (1600, 1000), (26, 18, 16))
    draw = ImageDraw.Draw(img)
    for y in range(1000):
        ratio = y / 1000
        r = int(26 + (128 - 26) * ratio * 0.6)
        g = int(18 + (28 - 18) * ratio)
        b = int(16 + (42 - 16) * ratio)
        draw.line([(0, y), (1600, y)], fill=(r, g, b))
    draw.ellipse([900, -100, 1700, 700], fill=(201, 162, 39, ))
    # Approximate gold glow
    for i in range(8):
        alpha_box = [950 + i * 10, 50 + i * 10, 1550 - i * 10, 650 - i * 10]
        draw.ellipse(alpha_box, outline=(201, 162, 39))
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=88, method=4)
    return ContentFile(buf.getvalue(), name="hero.webp")


def try_download_logo(url: str) -> ContentFile | None:
    try:
        import requests

        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and resp.content:
            # Normalize downloads to WebP when possible
            try:
                pil = Image.open(io.BytesIO(resp.content)).convert("RGB")
                out = io.BytesIO()
                pil.save(out, format="WEBP", quality=90, method=4)
                return ContentFile(out.getvalue(), name="logo.webp")
            except Exception:
                return ContentFile(resp.content, name="logo.webp")
    except Exception:
        return None
    return None


class Command(BaseCommand):
    help = "Seed DESI VIBES catalog, demo users, and store settings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Clear catalog products/variants before seeding",
        )
        parser.add_argument(
            "--per-category",
            type=int,
            default=PRODUCTS_PER_CATEGORY,
            help="Products per category (default 5)",
        )
        parser.add_argument(
            "--logo-url",
            type=str,
            default="",
            help="Optional URL to download brand logo",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        per_cat = options["per_category"]
        if options["reset"]:
            self.stdout.write("Clearing catalog…")
            ProductVariant.objects.all().delete()
            ProductImage.objects.all().delete()
            Product.objects.all().delete()

        self._seed_settings(options.get("logo_url") or "")
        self._seed_users()
        sizes = self._seed_sizes()
        colours = self._seed_colours()
        categories = self._seed_categories()

        rng = random.Random(42)
        total_products = 0
        total_variants = 0

        for cat_meta, category in zip(CATEGORIES, categories):
            existing = Product.objects.filter(category=category).count()
            to_create = max(0, per_cat - existing)
            self.stdout.write(f"Seeding {to_create} products for {category.name}…")
            for i in range(to_create):
                name = self._unique_name(cat_meta, rng, category)
                lo, hi = cat_meta["price_range"]
                price = Decimal(rng.randint(lo, hi))
                # Round to 99 endings
                price = Decimal(int(price) // 100 * 100 + 99)

                product = Product.objects.create(
                    name=name,
                    category=category,
                    description=self._description(name, category.name),
                    base_price=price,
                    is_active=True,
                    is_featured=(i < 3),
                    hsn_code="6203",
                )

                # One primary image by default (admin can add more later)
                product_colours = rng.sample(list(colours), k=COLOURS_PER_PRODUCT)
                primary_colour = product_colours[0]
                content = generate_product_image(name, primary_colour.hex)
                ProductImage.objects.create(
                    product=product,
                    image=content,
                    alt=f"{name} — {product_colours[0].name} mens {category.name.lower()}",
                    sort_order=0,
                    is_primary=True,
                )
                # Mirror first gallery image as featured for CMS editing
                first_img = product.images.filter(is_primary=True).first()
                if first_img:
                    Product.objects.filter(pk=product.pk).update(
                        featured_image=first_img.image.name
                    )

                for size in sizes:
                    for colour in product_colours:
                        sku = f"DV-{category.slug[:3].upper()}-{product.pk:04d}-{size.code}-{colour.name[:3].upper()}"
                        ProductVariant.objects.create(
                            product=product,
                            size=size,
                            colour=colour,
                            sku=sku,
                            stock_qty=rng.randint(3, 40),
                            is_active=True,
                        )
                        total_variants += 1
                total_products += 1

            # Category image from first product if missing
            if not category.image:
                first = (
                    Product.objects.filter(category=category)
                    .prefetch_related("images")
                    .first()
                )
                if first and first.primary_image:
                    category.image = first.primary_image.image
                    category.save(update_fields=["image"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Products added this run: {total_products}, variants: {total_variants}"
            )
        )
        self.stdout.write("Admin: admin / DemoAdmin@123")
        self.stdout.write("Buyer: buyer / DemoBuyer@123")

    def _seed_settings(self, logo_url: str):
        store = StoreSettings.load()
        store.store_name = "DESI VIBES"
        store.tagline = "Modern Ethnic Wear for Men"
        store.theme_color = "#801C2A"
        store.currency = "INR"
        store.cod_enabled = True
        store.prepaid_enabled = False
        store.gst_enabled = False
        store.free_shipping_over = Decimal("2999")
        store.flat_shipping_rate = Decimal("99")
        store.support_email = "hello@desivibes.demo"
        store.support_phone = "+91 98765 43210"
        if not store.logo:
            content = try_download_logo(logo_url) if logo_url else None
            store.logo = content or generate_logo()
        store.save()

        # Also copy logo + hero into static/brand for templates
        brand_dir = Path(settings.BASE_DIR) / "static" / "brand"
        brand_dir.mkdir(parents=True, exist_ok=True)
        logo_static = brand_dir / "logo.webp"
        if not logo_static.exists() and store.logo:
            logo_static.write_bytes(store.logo.read())
            store.logo.seek(0)
        hero_static = brand_dir / "hero.webp"
        if not hero_static.exists():
            hero = generate_hero()
            hero_static.write_bytes(hero.read())

    def _seed_users(self):
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@desivibes.demo",
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Admin",
            },
        )
        if created:
            admin.set_password("DemoAdmin@123")
            admin.save()
        else:
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password("DemoAdmin@123")
            admin.save()

        buyer, created = User.objects.get_or_create(
            username="buyer",
            defaults={
                "email": "buyer@desivibes.demo",
                "first_name": "Aarav",
                "last_name": "Sharma",
            },
        )
        if created or True:
            buyer.set_password("DemoBuyer@123")
            buyer.save()
        Customer.objects.get_or_create(
            user=buyer,
            defaults={
                "email": buyer.email,
                "full_name": "Aarav Sharma",
                "phone": "9876543210",
            },
        )

    def _seed_sizes(self):
        sizes = []
        for code, order in SIZES:
            obj, _ = Size.objects.get_or_create(
                code=code, defaults={"sort_order": order}
            )
            sizes.append(obj)
        return sizes

    def _seed_colours(self):
        colours = []
        for name, hex_code, order in COLOURS:
            obj, _ = Colour.objects.get_or_create(
                name=name, defaults={"hex": hex_code, "sort_order": order}
            )
            colours.append(obj)
        return colours

    def _seed_categories(self):
        cats = []
        for meta in CATEGORIES:
            obj, _ = Category.objects.get_or_create(
                slug=meta["slug"],
                defaults={
                    "name": meta["name"],
                    "description": meta["description"],
                    "sort_order": meta["sort_order"],
                    "is_active": True,
                },
            )
            cats.append(obj)
        return cats

    def _unique_name(self, meta, rng, category) -> str:
        for _ in range(50):
            name = f"{rng.choice(meta['prefixes'])} {rng.choice(meta['suffixes'])}"
            if not Product.objects.filter(name=name, category=category).exists():
                return name
        return f"{meta['prefixes'][0]} {meta['suffixes'][0]} {rng.randint(100,999)}"

    def _description(self, name: str, category: str) -> str:
        return (
            f"{name} from the DESI VIBES {category} collection. "
            f"Modern ethnic tailoring with a royal finish — ideal for celebrations, "
            f"receptions, and elevated everyday wear. Soft hand-feel fabric, "
            f"precise stitches, and a silhouette that balances tradition with contemporary ease.\n\n"
            f"Pair with classic mojaris or leather loafers. Dry clean recommended."
        )
