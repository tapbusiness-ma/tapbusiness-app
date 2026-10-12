from decimal import Decimal

from django.test import TestCase

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