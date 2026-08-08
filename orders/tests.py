"""Happy-path tests for cart and COD checkout."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from accounts.models import Customer
from catalog.models import Category, Colour, Product, ProductVariant, Size
from core.models import StoreSettings
from orders.models import Order


class CheckoutFlowTests(TestCase):
    def setUp(self):
        StoreSettings.load()
        self.user = User.objects.create_user(
            username="tester", password="TestPass123!", email="t@example.com"
        )
        Customer.objects.create(
            user=self.user, email="t@example.com", full_name="Test User", phone="9876543210"
        )
        cat = Category.objects.create(name="Kurtas", slug="kurtas-test")
        size = Size.objects.create(code="M", sort_order=1)
        colour = Colour.objects.create(name="Maroon", hex="#801C2A")
        product = Product.objects.create(
            name="Test Kurta",
            slug="test-kurta",
            category=cat,
            base_price=Decimal("1999.00"),
            is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            size=size,
            colour=colour,
            sku="TEST-M-MAR",
            stock_qty=10,
            is_active=True,
        )
        self.client = Client()

    def test_add_to_cart_and_place_order(self):
        self.assertTrue(self.client.login(username="tester", password="TestPass123!"))
        response = self.client.post(
            "/cart/add/", {"variant_id": self.variant.id, "qty": 2}
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            "/orders/checkout/",
            {
                "full_name": "Test User",
                "phone": "9876543210",
                "line1": "1 Demo Street",
                "line2": "",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
            },
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertTrue(order.order_number.startswith("DV-"))
        self.assertEqual(order.items.count(), 1)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 8)
