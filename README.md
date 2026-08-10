# DESI VIBES — Ethnic Wear Demo Store

Royal, modern e-commerce demo for men's Indian ethnic wear. Built with Django, HTMX, Tailwind CSS, Alpine.js, and django-unfold CMS.

## Quick start

```powershell
cd ethnic-wear
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # set DATABASE_URL to your Neon connection string
python manage.py migrate
python manage.py seed_catalog
python manage.py runserver
```

Open:

- Storefront: http://127.0.0.1:8000/
- Admin CMS: http://127.0.0.1:8000/admin/

## Demo credentials

| Role  | Username | Password        |
|-------|----------|-----------------|
| Admin | `admin`  | `DemoAdmin@123` |
| Buyer | `buyer`  | `DemoBuyer@123` |

## Client demo flow

1. **Admin** — Login at `/admin/` → Products → edit names, prices, stock, images, variants (size × colour).
2. **Buyer** — Login as `buyer` → Shop → open a product → pick size & colour → Add to Cart → Checkout → **Place Order** (COD).
3. Confirm the order appears under **Orders** in the admin and under **My Orders** on the storefront.

## Seed data

```powershell
python manage.py seed_catalog      # products + variants + images
python manage.py seed_content      # hero slides, reviews, about/craft, product details
```

`seed_content` is safe to re-run. Edit everything further in `/admin/`:

- **Products** — material, made in, fit, care, size chart, related products (You may also like), SEO fields
- **Hero slides** — slideshow images, titles, CTAs
- **Customer reviews** — homepage testimonials
- **Store settings** — About Us, Crafted in India, default size chart, SEO keywords

## SEO / ASO / GSO

- Meta title & description per page/product (CMS)
- Canonical URLs, Open Graph, Twitter cards
- `sitemap.xml` + `robots.txt` (incl. AI crawler allowances)
- JSON-LD: Organization, WebSite + SearchAction, Product, BreadcrumbList
- `manifest.webmanifest` for mobile home-screen / ASO-style discoverability
- Semantic HTML, breadcrumbs, structured product attributes (material, origin)

## Stack

- Django 5 + Neon Postgres (`DATABASE_URL`); SQLite fallback for local-only
- Vercel Blob for media uploads in production (`BLOB_READ_WRITE_TOKEN`)
- django-unfold admin theme
- HTMX cart updates
- Alpine.js variant picker
- Tailwind via CDN

## Media uploads on Vercel

Seeded demo images live under `media/` and are committed so `/media/...` works on Vercel.
Vercel’s app filesystem is read-only, so **new** admin uploads cannot write to `media/`.

1. In the [Vercel dashboard](https://vercel.com/dashboard) → your project → **Storage** → create a **Blob** store and connect it to this project.
2. Redeploy (Vercel injects `BLOB_READ_WRITE_TOKEN`).
3. Admin image uploads then go to Vercel Blob; local/dev without the token still uses `media/`.

## Deferred (configure later)

Razorpay payments, Shiprocket, Zoho CRM, PDF invoices — toggles exist on `StoreSettings` in admin.

## Project layout

```
config/          Django project settings
core/            StoreSettings
catalog/         Products, variants, seed command
cart/            Session + user cart
orders/          COD checkout & order history
accounts/        Login / register
templates/       Storefront templates
static/brand/    Logo & hero
media/           Uploaded / seeded images
docs/            PRD
```
