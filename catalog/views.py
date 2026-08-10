"""Catalog storefront views."""

import json

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from catalog.models import Category, Colour, Product, ProductVariant, Size
from core.models import CustomerReview, HeroSlide, StoreSettings


@require_GET
def home(request):
    categories = Category.objects.filter(is_active=True).order_by("sort_order")
    featured = (
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related("category")
        .prefetch_related("images")[:8]
    )
    bestsellers = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")[:12]
    )
    slides = list(HeroSlide.objects.filter(is_active=True)[:3])
    reviews = CustomerReview.objects.filter(is_featured=True)[:6]
    store = StoreSettings.load()
    return render(
        request,
        "catalog/home.html",
        {
            "categories": categories,
            "featured": featured,
            "bestsellers": bestsellers,
            "hero_slides": slides,
            "hero_images": [
                {
                    "desktop": "brand/hero-1.webp",
                    "mobile": "brand/hero-1-mobile.jpg",
                },
                {
                    "desktop": "brand/hero-2.webp",
                    "mobile": "brand/hero-2-mobile.jpg",
                },
                {
                    "desktop": "brand/hero-3.webp",
                    "mobile": "brand/hero-3-mobile.jpg",
                },
            ],
            "reviews": reviews,
            "seo_title": store.seo_title(),
            "seo_description": store.seo_description(),
            "canonical_path": "/",
            "og_type": "website",
        },
    )


@require_GET
def shop(request, slug=None):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images", "variants")
    )
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        products = products.filter(category=category)

    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(material__icontains=q)
        )

    size_codes = request.GET.getlist("size")
    colour_ids = request.GET.getlist("colour")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if size_codes:
        products = products.filter(
            variants__size__code__in=size_codes, variants__is_active=True
        ).distinct()
    if colour_ids:
        products = products.filter(
            variants__colour_id__in=colour_ids, variants__is_active=True
        ).distinct()
    if min_price:
        products = products.filter(base_price__gte=min_price)
    if max_price:
        products = products.filter(base_price__lte=max_price)

    sort = request.GET.get("sort", "newest")
    if sort == "price_asc":
        products = products.order_by("base_price")
    elif sort == "price_desc":
        products = products.order_by("-base_price")
    else:
        products = products.order_by("-created_at")

    if category:
        seo_title = category.meta_title or f"{category.name} for Men | DESI VIBES"
        seo_description = category.meta_description or (
            category.description
            or f"Shop {category.name} for men online at DESI VIBES. Wedding & festive ethnic wear crafted in India."
        )[:160]
        canonical_path = category.get_absolute_url()
    else:
        seo_title = "Shop Men's Ethnic Wear Online | Kurtas, Sherwanis & More"
        seo_description = (
            "Browse men's kurtas, sherwanis, bandhgalas and Nehru jackets at DESI VIBES. "
            "Filter by size, colour and price. Crafted in India."
        )
        canonical_path = "/shop/"

    context = {
        "products": products,
        "category": category,
        "categories": Category.objects.filter(is_active=True),
        "sizes": Size.objects.all(),
        "colours": Colour.objects.all(),
        "selected_sizes": size_codes,
        "selected_colours": [str(c) for c in colour_ids],
        "q": q,
        "sort": sort,
        "min_price": min_price or "",
        "max_price": max_price or "",
        "seo_title": seo_title,
        "seo_description": seo_description,
        "canonical_path": canonical_path,
    }
    template = (
        "catalog/partials/product_grid.html"
        if request.htmx
        else "catalog/shop.html"
    )
    return render(request, template, context)


@require_GET
def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related(
            "images",
            "related_products__images",
            "related_products__category",
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True).select_related(
                    "size", "colour"
                ),
            ),
        ),
        slug=slug,
        is_active=True,
    )
    variants = list(product.variants.all())
    sizes = sorted(
        {v.size for v in variants}, key=lambda s: (s.sort_order, s.code)
    )
    colours = sorted(
        {v.colour for v in variants}, key=lambda c: (c.sort_order, c.name)
    )
    variant_map = {
        f"{v.size_id}-{v.colour_id}": {
            "id": v.id,
            "sku": v.sku,
            "price": str(v.unit_price),
            "stock": v.stock_qty,
            "in_stock": v.in_stock,
        }
        for v in variants
    }
    related = list(
        product.related_products.filter(is_active=True).prefetch_related("images")[:4]
    )
    if not related:
        related = list(
            Product.objects.filter(category=product.category, is_active=True)
            .exclude(pk=product.pk)
            .prefetch_related("images")[:4]
        )

    size_chart_raw = product.effective_size_chart()
    size_chart_rows = _parse_size_chart(size_chart_raw)

    return render(
        request,
        "catalog/product.html",
        {
            "product": product,
            "sizes": sizes,
            "colours": colours,
            "variant_map_json": json.dumps(variant_map),
            "related": related,
            "size_chart_rows": size_chart_rows,
            "size_chart_raw": size_chart_raw,
            "seo_title": product.seo_title(),
            "seo_description": product.seo_description(),
            "canonical_path": product.get_absolute_url(),
            "og_type": "product",
            "og_image": product.primary_image.image.url if product.primary_image else "",
        },
    )


def _parse_size_chart(text: str) -> list[list[str]]:
    """Parse pipe- or tab-separated size chart into table rows."""
    rows = []
    for line in (text or "").strip().splitlines():
        line = line.strip()
        if not line or line.lower().startswith("tip:"):
            continue
        if "|" in line:
            cells = [c.strip() for c in line.split("|")]
        elif "\t" in line:
            cells = [c.strip() for c in line.split("\t")]
        else:
            continue
        if cells:
            rows.append(cells)
    return rows
