# PRD — Ethnic Wear E-commerce (Prototype → Prod)

**Version:** 1.0
**Goal:** A sleek, fast, mobile + desktop ethnic-wear store that is 70–80% production-ready, config-driven (client flips switches instead of touching code), and shippable to prod in ~7 days.
**Reusability:** This is prototype #1 in a catalogue. Everything client-specific lives in settings/config so the same codebase can be re-skinned for the next client.

---

## 1. Tech Stack & Architecture

**Chosen approach: Django monolith (recommended over headless for speed + easy handoff).**

| Layer | Choice | Why |
|---|---|---|
| Backend | **Django** (not Flask) | Built-in admin, ORM, auth = half the app for free |
| API (internal only) | Django views + **HTMX** partials | App-like updates (cart, filters) without full reloads |
| Frontend | **Tailwind CSS** + **Alpine.js** | Modern, fast, no separate build app to deploy |
| DB | **PostgreSQL** | Prod-grade; SQLite only for local dev |
| Images | Cloudinary **or** local + `django-imagekit` | Responsive/optimized images = fast fashion catalogue |
| Invoices | **WeasyPrint** (HTML→PDF) | Easy to brand, GST-aware templates |
| Payments | **Razorpay Standard Checkout** | Popup; Razorpay holds card data (no PCI on us) |
| Shipping | **Shiprocket API** (optional) | Auto tracking + SMS/email/WhatsApp + COD support |
| CRM | **Zoho CRM** (optional) → Excel fallback | Config-driven sink |
| Deploy | Railway / Render / Fly.io + managed Postgres | One deploy target |

> If a future client explicitly wants a full SPA, swap the frontend for Next.js + DRF. The data model and business logic below are unchanged.

---

## 2. Config Toggles ("click of a button")

A single `StoreSettings` record (Django admin) drives client-specific behavior. No redeploy needed.

| Toggle | Effect |
|---|---|
| `gst_enabled` | ON → invoices compute CGST/SGST/IGST, show GSTIN + HSN. OFF → simple invoice. |
| `gstin`, `default_gst_rate`, `default_hsn` | Filled only when GST is on |
| `cod_enabled` / `prepaid_enabled` | Show/hide payment options at checkout (both ON by default) |
| `crm_provider` = `none` / `zoho` | `zoho` → push invoice to Zoho; `none` → append to local Excel |
| `zoho_client_id/secret/refresh_token` | Zoho OAuth creds (blank = fallback to Excel) |
| `shiprocket_enabled` + creds | ON → auto-create shipments + sync tracking. OFF → admin updates status manually. |
| `store_name`, `logo`, `theme_color`, `currency` | Branding per client (default INR) |
| `free_shipping_over`, `flat_shipping_rate` | Shipping charge rules |

**Design rule:** every integration is behind a small interface with a no-op/local fallback, so a half-configured store still works end-to-end.

---

## 3. Data Model

```
StoreSettings (singleton)
  store_name, logo, theme_color, currency
  gst_enabled, gstin, default_gst_rate, default_hsn
  cod_enabled, prepaid_enabled
  crm_provider, zoho_* creds
  shiprocket_enabled, shiprocket_* creds
  free_shipping_over, flat_shipping_rate

Category
  name, slug, parent (self-FK, optional), is_active

Product
  name, slug, description, category (FK)
  base_price, hsn_code (opt), gst_rate (opt), is_active
  → images: ProductImage[]  (image, alt, sort_order)

# Sizes & colours are DATA, not code — bigger clients just add rows
Size    (code: XS/S/M/L/XL/XXL, sort_order)
Colour  (name, hex, sort_order)          # 8+ supported, no cap

ProductVariant
  product (FK), size (FK), colour (FK)
  sku (unique), price_override (opt), stock_qty, is_active
  # unique_together = (product, size, colour)

Customer            # extends Django User; guests have no account
  user (FK, nullable), phone, email
Address
  customer (FK, nullable), full_name, phone, line1, line2,
  city, state, pincode, is_default

Cart / CartItem
  cart: session_key or customer
  item: variant (FK), qty

Order
  order_number (unique), customer (FK, nullable)
  guest_name, guest_email, guest_phone         # for guest checkout
  status  → Placed/Confirmed/Packed/Shipped/OutForDelivery/Delivered/Cancelled
  subtotal, tax_total, shipping_total, grand_total
  payment_method (cod/prepaid), payment_status (pending/paid/failed/refunded)
  shipping_address (FK), created_at
OrderItem
  order (FK), variant (FK), qty
  unit_price, tax_rate, tax_amount, line_total   # snapshot at purchase

Payment
  order (FK), provider='razorpay'
  razorpay_order_id, razorpay_payment_id, signature_verified (bool)
  amount, status
  # COD orders create a Payment with status=pending until delivery

Invoice
  order (FK), invoice_number (unique), pdf_file
  is_gst_invoice, tax_breakup (json)
  crm_synced (bool), crm_reference, synced_to_excel (bool)

Shipment
  order (FK), shiprocket_order_id, awb, courier
  tracking_url, current_status, status_history (json)

Coupon (Phase 2)
  code, type (pct/flat), value, min_order, active, expires_at
```

---

## 4. Feature Scope

**Storefront (buyer)**
- Home / category / product pages; search + filter by category, size, colour, price
- Product page with variant picker (size + colour), stock awareness, image gallery
- Cart (HTMX add/update/remove, no reload)
- **Guest checkout + optional account creation** at the end (one click, reuse entered email/phone)
- Checkout: address → order review → pay
- Order tracking page: logged-in via account; guests via order # + phone/email

**Payments**
- Razorpay Standard Checkout popup for prepaid (UPI Intent/QR, cards, netbanking, wallets)
- **Server-side webhook + signature verification** is the source of truth — never trust the browser callback
- COD path (creates pending Payment, no gateway call)
- ⚠️ UPI *Collect* (manual VPA entry) is deprecated from 28 Feb 2026 — Razorpay checkout handles this; don't build Collect flows.

**Order management (back-office = one Django admin login)**
- Product/variant CMS (add product, set variants, stock, images, prices)
- Orders section: list, filter by status, update status, view payment, (re)generate invoice
- Theme: `django-unfold` so it looks modern for non-technical staff
- Roles: staff vs superuser permissions

**Order tracking (NO GPS)**
- Status-based lifecycle, updated from admin
- If `shiprocket_enabled`: auto-create shipment on "Packed", pull AWB + tracking URL, sync status via webhook/poll, auto SMS/email/WhatsApp to customer

**Invoicing**
- On payment success (or order confirm for COD), generate branded PDF
- GST-aware per `gst_enabled`
- Send to sink: Zoho CRM if configured, else append row to local Excel/CSV

**Notifications**
- Order confirmation via email (SMTP); SMS/WhatsApp via Shiprocket when enabled

---

## 5. Non-Functional Requirements

- **Performance:** lazy-loaded responsive images, server-rendered pages, minimal JS. Target LCP < 2.5s on 4G.
- **SEO:** server-rendered HTML, clean slugs, meta tags, sitemap.
- **Security:** secrets in env vars; CSRF on; Razorpay webhook signature verified; never store raw card data; rate-limit checkout.
- **Legal pages** (required for Razorpay activation): T&C, Privacy, Returns, Shipping policy — editable in admin.

---

## 6. 7-Day Build Plan

| Day | Deliverable |
|---|---|
| 1 | Project scaffold, `StoreSettings`, models, Django admin + `django-unfold`, seed sizes/colours |
| 2 | Storefront: home/category/product pages, Tailwind design system, image handling |
| 3 | Cart (HTMX), variant selection, stock logic |
| 4 | Checkout flow: address, review, guest + account; Razorpay integration + **webhook verify** |
| 5 | COD path, order lifecycle, order-management views, tracking page |
| 6 | Invoice PDF (GST toggle), Zoho/Excel sink, email notifications, legal pages |
| 7 | Shiprocket integration (behind toggle), polish, seed demo data, deploy to staging |

**Scope discipline:** Coupons, wishlist, reviews, analytics dashboards, multi-warehouse = **Phase 2**. Keep them out to protect the 7-day target.

---

## 7. Out of Scope (Phase 2+)
Wishlist/save-for-later, coupons & festive sales engine, product reviews, abandoned-cart recovery, advanced analytics, multi-currency, loyalty, multi-vendor.
