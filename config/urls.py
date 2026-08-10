from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve

from core.seo import CategorySitemap, ProductSitemap, StaticViewSitemap, robots_txt

sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("robots.txt", robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "manifest.webmanifest",
        TemplateView.as_view(
            template_name="manifest.webmanifest",
            content_type="application/manifest+json",
        ),
        name="webmanifest",
    ),
    path(
        "legal/terms/",
        TemplateView.as_view(template_name="legal/terms.html"),
        name="legal_terms",
    ),
    path(
        "legal/privacy/",
        TemplateView.as_view(template_name="legal/privacy.html"),
        name="legal_privacy",
    ),
    path(
        "legal/returns/",
        TemplateView.as_view(template_name="legal/returns.html"),
        name="legal_returns",
    ),
    path(
        "legal/shipping/",
        TemplateView.as_view(template_name="legal/shipping.html"),
        name="legal_shipping",
    ),
    path("", include("catalog.urls")),
]

# Packaged demo media must be reachable on Vercel (read-only FS, DEBUG often off).
# Absolute Vercel Blob URLs never hit this route; only relative /media/... paths do.
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
