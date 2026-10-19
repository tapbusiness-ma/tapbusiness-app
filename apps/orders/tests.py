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
                args=[self.restaurant.slug, order.id, order.token],
            ),
        )
        self.assertEqual(order.subtotal, Decimal("35.00"))
        self.assertEqual(order.delivery_fee, Decimal("7.50"))
        self.assertEqual(order.total, Decimal("42.50"))
        self.assertEqual(item.unit_price, Decimal("35.00"))
        success_response = self.client.get(
            reverse(
                "orders:order_success",
                args=[self.restaurant.slug, order.id, order.token],
            )
        )
        self.assertEqual(success_response.status_code, 200)
        self.assertContains(success_response, "0612345678")
        # بلا الرمز أولا برمز غالط → 404 (حماية بيانات الزبون)
        no_token = self.client.get(
            f"/m/{self.restaurant.slug}/order/{order.id}/ok/"
        )
        self.assertEqual(no_token.status_code, 404)
        bad_token = self.client.get(
            reverse(
                "orders:order_success",
                args=[self.restaurant.slug, order.id, "رمز-غالط"],
            )
        )
        self.assertEqual(bad_token.status_code, 404)
        self.assertEqual(self.client.session.get(f"cart_{self.restaurant.id}"), None)

    def test_adding_to_cart_requires_post(self):
        response = self.client.get(
            reverse(
                "orders:cart_add",
                args=[self.restaurant.slug, self.product.id],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_checkout_uses_table_number_from_session(self):
        session = self.client.session
        session[f"table_{self.restaurant.id}"] = "T7"
        session.save()
        self.client.post(
            reverse(
                "orders:cart_add",
                args=[self.restaurant.slug, self.product.id],
            )
        )

        self.client.post(
            reverse("orders:checkout", args=[self.restaurant.slug]),
            {
                "customer_name": "Table Customer",
                "customer_phone": "0611111111",
                "address": "",
            },
        )

        order = Order.objects.get()
        self.assertEqual(order.order_type, Order.OrderType.TABLE)
        self.assertEqual(order.table_number, "T7")
class OrderTokenSecurityTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="R", slug="r")
        self.order = Order.objects.create(
            restaurant=self.restaurant,
            customer_name="Sara",
            customer_phone="0611223344",
        )

    def test_tokens_are_unique_per_order(self):
        other = Order.objects.create(
            restaurant=self.restaurant, customer_name="X", customer_phone="06"
        )
        self.assertNotEqual(self.order.token, other.token)

    def test_success_page_needs_valid_token(self):
        url = reverse(
            "orders:order_success",
            args=[self.restaurant.slug, self.order.id, self.order.token],
        )
        self.assertEqual(self.client.get(url).status_code, 200)
        bad = reverse(
            "orders:order_success",
            args=[self.restaurant.slug, self.order.id, "nope"],
        )
        self.assertEqual(self.client.get(bad).status_code, 404)


class DeliveryFeeTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name="R", slug="r", delivery_fee=Decimal("10.00")
        )
        self.product = Product.objects.create(
            restaurant=self.restaurant, name="Tacos", price=Decimal("35.00")
        )

    def _order(self, table=None):
        if table:
            session = self.client.session
            session[f"table_{self.restaurant.id}"] = table
            session.save()
        self.client.post(
            reverse("orders:cart_add", args=[self.restaurant.slug, self.product.id])
        )
        self.client.post(
            reverse("orders:checkout", args=[self.restaurant.slug]),
            {"customer_name": "C", "customer_phone": "06", "address": "Rue"},
        )
        return Order.objects.latest("id")

    def test_delivery_order_has_fee(self):
        order = self._order()
        self.assertEqual(order.order_type, Order.OrderType.DELIVERY)
        self.assertEqual(order.delivery_fee, Decimal("10.00"))
        self.assertEqual(order.total, Decimal("45.00"))

    def test_table_order_has_no_fee(self):
        order = self._order(table="T3")
        self.assertEqual(order.order_type, Order.OrderType.TABLE)
        self.assertEqual(order.delivery_fee, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("35.00"))


class StatusTransitionTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="R", slug="r")
        from django.contrib.auth.models import User

        from apps.restaurants.models import Membership

        self.user = User.objects.create_user("owner", password="x")
        Membership.objects.create(
            user=self.user,
            restaurant=self.restaurant,
            role=Membership.Roles.OWNER,
        )
        self.order = Order.objects.create(
            restaurant=self.restaurant, customer_name="C", customer_phone="06"
        )
        self.client.force_login(self.user)
        self.url = reverse(
            "orders:owner_order_status", args=[self.restaurant.slug, self.order.id]
        )

    def _set_status(self, new):
        self.client.post(self.url, {"status": new})
        self.order.refresh_from_db()
        return self.order.status

    def test_valid_chain(self):
        for nxt in ["confirmed", "preparing", "ready", "delivered"]:
            self.assertEqual(self._set_status(nxt), nxt)

    def test_skip_is_rejected(self):
        self.assertEqual(self._set_status("delivered"), "pending")

    def test_cancel_then_terminal(self):
        self.assertEqual(self._set_status("cancelled"), "cancelled")
        self.assertEqual(self._set_status("confirmed"), "cancelled")

    def test_delivered_is_terminal(self):
        self.order.status = Order.Status.DELIVERED
        self.order.save()
        self.assertEqual(self._set_status("pending"), "delivered")


class CartCapTests(TestCase):
    def test_quantity_capped_per_product(self):
        from django.test import RequestFactory

        from .cart import Cart

        request = RequestFactory().get("/")
        request.session = self.client.session
        restaurant = Restaurant.objects.create(name="R", slug="r")
        cart = Cart(request, restaurant)
        for _ in range(30):
            cart.add(5)
        self.assertEqual(cart.data["5"], 20)


class OwnerOrdersPaginationTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        from apps.restaurants.models import Membership

        self.restaurant = Restaurant.objects.create(name="R", slug="r")
        self.user = User.objects.create_user("owner", password="x")
        Membership.objects.create(
            user=self.user,
            restaurant=self.restaurant,
            role=Membership.Roles.OWNER,
        )
        for i in range(25):
            Order.objects.create(
                restaurant=self.restaurant,
                customer_name=f"C{i}",
                customer_phone="06",
            )
        self.client.force_login(self.user)
        self.url = reverse("orders:owner_orders", args=[self.restaurant.slug])

    def test_pagination(self):
        page1 = self.client.get(self.url)
        self.assertEqual(len(page1.context["page_obj"]), 20)
        page2 = self.client.get(self.url + "?page=2")
        self.assertEqual(len(page2.context["page_obj"]), 5)

    def test_search_by_name(self):
        resp = self.client.get(self.url + "?q=C24")
        self.assertEqual(len(resp.context["page_obj"]), 1)
