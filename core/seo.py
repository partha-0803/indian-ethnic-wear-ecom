"""SEO helpers: sitemaps, robots, structured data."""

from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.urls import reverse

from catalog.models import Category, Product


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["catalog:home", "catalog:shop", "legal_terms", "legal_privacy", "legal_returns", "legal_shipping"]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True).select_related("category")

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /cart/",
        "Disallow: /orders/checkout/",
        "Disallow: /accounts/",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
        "",
        "# Generative / AI crawlers welcome for public catalogue pages",
        "User-agent: GPTBot",
        "Allow: /",
        "Allow: /shop/",
        "Allow: /product/",
        "Disallow: /admin/",
        "Disallow: /cart/",
        "Disallow: /accounts/",
        "",
        "User-agent: Google-Extended",
        "Allow: /",
        "Disallow: /admin/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
