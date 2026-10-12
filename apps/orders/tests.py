from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.menu.models import Product
from apps.restaurants.models import Restaurant
from .models import Order, OrderItem


class OrderItemSnapshotTests(TestCase):
    def test_item_keeps_name_and_price_snapshot_after_product_changes(self):
        restaurant = Restaurant.objects.create(name="Resto", slug="resto")
        product = Product.objects.create(
            restaurant=restaurant,
            name="Chicken Tacos",
            price=Decimal("35.00"),
        )
        order = Order.objects.create(
            restaurant=restaurant,
            customer_name="Customer",
            customer_phone="0600000000",
        )
        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=2,
        )

        product.name = "Premium Tacos"
        product.price = Decimal("50.00")
        product.save(update_fields=["name", "price"])
        item.refresh_from_db()

        self.assertEqual(item.product_name, "Chicken Tacos")
        self.assertEqual(item.unit_price, Decimal("35.00"))
        self.assertEqual(item.line_total, Decimal("70.00"))


class CheckoutFlowTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name="Checkout Resto",
            slug="checkout-resto",
            delivery_fee=Decimal("7.50"),
        )
        self.product = Product.objects.create(
            restaurant=self.restaurant,
            name="Tacos",
            price=Decimal("35.00"),
        )

    def test_cart_checkout_ignores_client_price_and_saves_server_snapshot(self):
        add_response = self.client.post(
            reverse(
                "orders:cart_add",
                args=[self.restaurant.slug, self.product.id],
            )
        )
        self.assertRedirects(
            add_response, reverse("orders:cart", args=[self.restaurant.slug])
        )

        checkout_response = self.client.post(
            reverse("orders:checkout", args=[self.restaurant.slug]),
            {
                "customer_name": "Test Customer",
                "customer_phone": "0612345678",
                "address": "Test address",
                "price": "0.01",
                "total": "0.01",
            },
        )

        order = Order.objects.get()
        item = order.items.get()
        self.assertRedirects(
            checkout_response,
            reverse(
                "orders:order_success",
                args=[self.restaurant.slug, order.id],
            ),
        )
        self.assertEqual(order.subtotal, Decimal("35.00"))
        self.assertEqual(order.delivery_fee, Decimal("7.50"))
        self.assertEqual(order.total, Decimal("42.50"))
        self.assertEqual(item.unit_price, Decimal("35.00"))
        success_response = self.client.get(
            reverse(
                "orders:order_success",
                args=[self.restaurant.slug, order.id],
            )
        )
        self.assertEqual(success_response.status_code, 200)
        self.assertContains(success_response, "0612345678")
        self.assertEqual(self.client.session.get(f"cart_{self.restaurant.id}"), None)

    def test_adding_to_cart_requires_post(self):
        response = self.client.get(
            reverse(
                "orders:cart_add",
                args=[self.restaurant.slug, self.product.id],
            )
        )

        self.assertEqual(response.status_code, 405)