"""
Enrich CMS content: product details, hero slides, reviews, about/craft imagery.

Safe to re-run. Does not delete products.

    python manage.py seed_content
"""

from __future__ import annotations

import io
import random
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from catalog.models import Product
from core.models import CustomerReview, HeroSlide, StoreSettings

MATERIALS = [
    "Silk blend",
    "Cotton silk",
    "Premium linen",
    "Brocade",
    "Velvet",
    "Chanderi weave",
    "Art silk",
    "Raw silk",
]
FITS = ["Regular fit", "Slim festive fit", "Relaxed silhouette", "Tailored cut"]
CARE = (
    "Dry clean only for best results.\n"
    "Store on a padded hanger away from direct sunlight.\n"
    "Steam lightly before wear; avoid high-heat ironing on embroidery.\n"
    "Do not bleach. Spot clean delicate areas with care."
)
EXTRA = (
    "Designed for weddings, receptions, and festive gatherings.\n"
    "Pair with classic mojaris or leather loafers.\n"
    "Model styling is illustrative; colour may vary slightly by screen."
)

REVIEWS = [
    ("Rohan Mehta", "Mumbai", 5, "The sherwani fit was immaculate. Felt royal without being heavy — perfect for my cousin's wedding."),
    ("Arjun Patel", "Ahmedabad", 5, "DESI VIBES kurtas are my go-to for Diwali. Fabric quality surprised me at this price."),
    ("Kabir Singh", "Delhi", 4, "Bandhgala stitching is clean and modern. Ordered a second colour the next week."),
    ("Vikram Rao", "Bengaluru", 5, "Nehru jacket arrived well packed. Size chart was accurate — rare online."),
    ("Ishaan Kapoor", "Jaipur", 5, "Love that it's made in India and still looks so contemporary. Compliments all evening."),
    ("Aditya Nair", "Hyderabad", 4, "Smooth checkout demo experience and the product page details helped me choose the right size."),
]

HERO_COPY = [
    ("DESI VIBES", "Modern ethnic wear for men — sherwanis that command the room.", "Shop Sherwanis", "/shop/sherwanis/"),
    ("Wedding Edit", "Regal silhouettes in gold, maroon, and midnight.", "Explore Collection", "/shop/"),
    ("Crafted in India", "From Jaipur looms to your celebration wardrobe.", "Shop Kurtas", "/shop/kurtas/"),
]


def _font(size: int):
    for name in ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"):
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def generate_model_slide(label: str, palette: tuple, width=1600, height=1000) -> ContentFile:
    """Stylized full-bleed image suggesting a model in sherwani/kurta."""
    bg, accent, cloth = palette
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    for y in range(height):
        r = int(bg[0] + (accent[0] - bg[0]) * (y / height) * 0.4)
        g = int(bg[1] + (accent[1] - bg[1]) * (y / height) * 0.4)
        b = int(bg[2] + (accent[2] - bg[2]) * (y / height) * 0.4)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Soft light
    draw.ellipse([width * 0.45, -200, width * 1.1, 500], outline=accent, width=2)

    # Model silhouette (right third)
    cx = int(width * 0.68)
    # Head
    draw.ellipse([cx - 55, 180, cx + 55, 290], fill=(40, 28, 24))
    # Torso / sherwani
    draw.rounded_rectangle([cx - 110, 280, cx + 110, 780], radius=20, fill=cloth)
    # Split colour panel (sherwani vibe)
    draw.rectangle([cx, 300, cx + 100, 760], fill=accent)
    # Collar
    draw.polygon([(cx - 50, 280), (cx, 330), (cx + 50, 280)], fill=bg)
    # Buttons
    for i in range(6):
        by = 360 + i * 55
        draw.ellipse([cx + 8, by, cx + 20, by + 12], fill=(26, 18, 16))
    # Arms
    draw.polygon([(cx - 110, 320), (cx - 180, 620), (cx - 130, 640), (cx - 110, 400)], fill=cloth)
    draw.polygon([(cx + 110, 320), (cx + 180, 620), (cx + 130, 640), (cx + 110, 400)], fill=accent)
    # Legs hint
    draw.rectangle([cx - 70, 780, cx - 15, 960], fill=(30, 22, 20))
    draw.rectangle([cx + 15, 780, cx + 70, 960], fill=(30, 22, 20))

    # Gold frame accent
    draw.rectangle([40, 40, width - 40, height - 40], outline=(201, 162, 39), width=2)

    font = _font(28)
    draw.text((80, height - 100), label, fill=(245, 240, 230), font=font)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return ContentFile(buf.getvalue(), name=f"hero-{label[:20].replace(' ', '-').lower()}.jpg")


def generate_section_image(title: str, colours, width=1200, height=1500) -> ContentFile:
    img = Image.new("RGB", (width, height), colours[0])
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / height
        r = int(colours[0][0] * (1 - t) + colours[1][0] * t)
        g = int(colours[0][1] * (1 - t) + colours[1][1] * t)
        b = int(colours[0][2] * (1 - t) + colours[1][2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    draw.rectangle([48, 48, width - 48, height - 48], outline=(201, 162, 39), width=3)
    font = _font(42)
    draw.text((width // 2, height // 2), title, fill=(245, 240, 230), font=font, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return ContentFile(buf.getvalue(), name=f"{title.lower().replace(' ', '-')}.jpg")


class Command(BaseCommand):
    help = "Seed homepage content, hero slides, reviews, and product detail fields"

    @transaction.atomic
    def handle(self, *args, **options):
        store = StoreSettings.load()
        store.meta_title = "DESI VIBES — Modern Ethnic Wear for Men"
        store.meta_description = (
            "Shop premium sherwanis, kurtas, bandhgalas and Nehru jackets. "
            "Crafted in India. Size charts, care guides, and COD checkout."
        )
        store.about_title = "Our Story"
        store.about_body = (
            "DESI VIBES was born from a love of Indian craft and modern silhouette. "
            "We design ethnic wear for men who want tradition with a contemporary edge—"
            "sharper cuts, richer fabrics, and colours that feel royal without the noise.\n\n"
            "Every collection is built to move from mandap to after-party with ease."
        )
        store.craft_title = "Crafted in India"
        store.craft_body = (
            "Every piece is cut and finished in India by skilled artisans. "
            "From Banarasi-inspired weaves to contemporary bandhgalas, our ateliers "
            "in Rajasthan and Uttar Pradesh bring heritage techniques into wearable luxury.\n\n"
            "We work closely with weaving clusters so provenance stays on the label—and in the feel."
        )
        store.craft_locations = "Jaipur · Varanasi · New Delhi"
        if not store.about_image:
            store.about_image = generate_section_image(
                "DESI VIBES", ((128, 28, 42), (26, 18, 16))
            )
        if not store.craft_image:
            store.craft_image = generate_section_image(
                "Made in India", ((26, 18, 16), (201, 162, 39))
            )
        store.save()
        self.stdout.write("Updated Store Settings (about, craft, SEO)")

        # Hero slides (copy/titles only — storefront uses static/brand/hero-1..3.jpg)
        if not HeroSlide.objects.exists():
            for i, (title, subtitle, cta, url) in enumerate(HERO_COPY):
                HeroSlide.objects.create(
                    title=title,
                    subtitle=subtitle,
                    cta_label=cta,
                    cta_url=url,
                    sort_order=i,
                    is_active=True,
                    # Placeholder; homepage renders static brand/hero-*.jpg
                    image=generate_section_image(title, ((26, 18, 16), (128, 28, 42)), 800, 500),
                )
            self.stdout.write(f"Created {len(HERO_COPY)} hero slide titles (images from static/brand)")
        else:
            self.stdout.write("Hero slides already exist — skipped")

        # Reviews
        if not CustomerReview.objects.exists():
            for i, (name, loc, rating, quote) in enumerate(REVIEWS):
                CustomerReview.objects.create(
                    customer_name=name,
                    location=loc,
                    rating=rating,
                    quote=quote,
                    is_featured=True,
                    sort_order=i,
                )
            self.stdout.write(f"Created {len(REVIEWS)} reviews")
        else:
            self.stdout.write("Reviews already exist — skipped")

        # Product detail fields
        rng = random.Random(7)
        updated = 0
        products = list(Product.objects.all())
        for p in products:
            dirty = False
            if not p.material:
                p.material = rng.choice(MATERIALS)
                dirty = True
            if not p.made_in:
                p.made_in = "India"
                dirty = True
            if not p.fit:
                p.fit = rng.choice(FITS)
                dirty = True
            if not p.care_instructions:
                p.care_instructions = CARE
                dirty = True
            if not p.details_extra:
                p.details_extra = EXTRA
                dirty = True
            if not p.meta_title:
                p.meta_title = f"{p.name} | {p.category.name} | DESI VIBES"[:70]
                dirty = True
            if not p.meta_description:
                p.meta_description = (
                    f"Buy {p.name} in {p.material}. Made in {p.made_in}. "
                    f"Size chart & care guide included. Shop ethnic wear at DESI VIBES."
                )[:160]
                dirty = True
            if dirty:
                p.save()
                updated += 1

        # Wire a few related products for featured items
        featured = list(Product.objects.filter(is_featured=True)[:8])
        for p in featured:
            if p.related_products.exists():
                continue
            cousins = list(
                Product.objects.filter(category=p.category, is_active=True)
                .exclude(pk=p.pk)[:4]
            )
            if cousins:
                p.related_products.set(cousins)

        self.stdout.write(self.style.SUCCESS(f"Updated product details on {updated} products"))

        # Copy about image to static if useful
        brand = Path(settings.BASE_DIR) / "static" / "brand"
        brand.mkdir(parents=True, exist_ok=True)
