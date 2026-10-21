from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order
from apps.restaurants.models import Membership, Restaurant
from apps.subscriptions.models import Plan, Subscription

from .models import LoyaltyTransaction, LoyaltyWallet
from .services import (
    award_points_for_order,
    loyalty_enabled,
    normalize_phone,
    points_for_subtotal,
)


def make_restaurant(slug, plan_slug=None, sub_status=None):
    restaurant = Restaurant.objects.create(name=slug, slug=slug, is_active=True)
    if plan_slug:
        Subscription.objects.create(
            restaurant=restaurant,
            plan=Plan.objects.get(slug=plan_slug),
            status=sub_status or Subscription.Status.ACTIVE,
        )
    return restaurant


def make_order(restaurant, subtotal, phone="0612345678",
               status=Order.Status.DELIVERED, fee="0"):
    return Order.objects.create(
        restaurant=restaurant,
        customer_name="Client Test",
        customer_phone=phone,
        subtotal=Decimal(subtotal),
        delivery_fee=Decimal(fee),
        total=Decimal(subtotal) + Decimal(fee),
        status=status,
    )


class PointsCalculationTests(TestCase):
    def test_points_boundaries(self):
        cases = [
            ("0", 0), ("9", 0), ("9.99", 0),
            ("10", 1), ("19.99", 1), ("29", 2),
            ("50", 5), ("125", 12), ("200", 20),
        ]
        for amount, expected in cases:
            with self.subTest(amount=amount):
                self.assertEqual(points_for_subtotal(Decimal(amount)), expected)

    def test_normalize_phone_variants(self):
        expected = "+212612345678"
        for raw in [
            "0612345678", "06 12 34 56 78", "06-12-34-56-78",
            "+212612345678", "+212 612-345-678",
            "00212612345678", "212612345678",
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_phone(raw), expected)


class AwardServiceTests(TestCase):
    def setUp(self):
        self.premium = make_restaurant("premium-resto", "premium")

    def wallet_of(self, restaurant, phone="+212612345678"):
        return LoyaltyWallet.objects.get(restaurant=restaurant, phone=phone)

    def test_delivered_premium_order_awards_points(self):
        order = make_order(self.premium, "125")
        awarded = award_points_for_order(order)
        self.assertEqual(awarded, 12)
        wallet = self.wallet_of(self.premium)
        self.assertEqual(wallet.balance, 12)
        tx = LoyaltyTransaction.objects.get(order=order)
        self.assertEqual(tx.kind, LoyaltyTransaction.Kind.EARN)
        self.assertEqual(tx.points, 12)
        self.assertEqual(tx.wallet, wallet)

    def test_below_threshold_awards_nothing(self):
        order = make_order(self.premium, "9.99")
        self.assertEqual(award_points_for_order(order), 0)
        self.assertFalse(LoyaltyWallet.objects.exists())
        self.assertFalse(LoyaltyTransaction.objects.exists())

    def test_delivery_fee_is_excluded_from_points(self):
        # 100 DH أطباق + 50 DH توصيل = 10 نقط (على subtotal فقط)
        order = make_order(self.premium, "100", fee="50")
        self.assertEqual(award_points_for_order(order), 10)

    def test_no_points_before_delivered(self):
        for status in [
            Order.Status.PENDING, Order.Status.CONFIRMED,
            Order.Status.PREPARING, Order.Status.READY,
            Order.Status.CANCELLED,
        ]:
            with self.subTest(status=status):
                order = make_order(self.premium, "100", status=status)
                self.assertEqual(award_points_for_order(order), 0)
        self.assertFalse(LoyaltyTransaction.objects.exists())

    def test_award_is_idempotent(self):
        order = make_order(self.premium, "50")
        self.assertEqual(award_points_for_order(order), 5)
        self.assertEqual(award_points_for_order(order), 0)
        self.assertEqual(self.wallet_of(self.premium).balance, 5)
        self.assertEqual(
            LoyaltyTransaction.objects.filter(order=order).count(), 1
        )

    def test_database_constraint_blocks_duplicate_earn(self):
        order = make_order(self.premium, "50")
        award_points_for_order(order)
        wallet = self.wallet_of(self.premium)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LoyaltyTransaction.objects.create(
                    wallet=wallet,
                    kind=LoyaltyTransaction.Kind.EARN,
                    points=5,
                    order=order,
                )

    def test_non_premium_plans_earn_nothing(self):
        for plan_slug in ["pro", "demo"]:
            with self.subTest(plan=plan_slug):
                resto = make_restaurant(f"{plan_slug}-resto", plan_slug)
                order = make_order(resto, "200")
                self.assertEqual(award_points_for_order(order), 0)
        self.assertFalse(LoyaltyWallet.objects.exists())

    def test_premium_without_active_subscription_earns_nothing(self):
        for status in [Subscription.Status.TRIAL,
                       Subscription.Status.PAST_DUE,
                       Subscription.Status.CANCELLED]:
            with self.subTest(status=status):
                resto = make_restaurant(
                    f"premium-{status}", "premium", sub_status=status
                )
                self.assertFalse(loyalty_enabled(resto))
                order = make_order(resto, "200")
                self.assertEqual(award_points_for_order(order), 0)
        self.assertFalse(LoyaltyWallet.objects.exists())

    def test_wallets_are_isolated_per_restaurant(self):
        other = make_restaurant("premium-other", "premium")
        order_a = make_order(self.premium, "100")
        order_b = make_order(other, "30")
        award_points_for_order(order_a)
        award_points_for_order(order_b)
        self.assertEqual(self.wallet_of(self.premium).balance, 10)
        self.assertEqual(self.wallet_of(other).balance, 3)

    def test_phone_variants_merge_into_one_wallet(self):
        first = make_order(self.premium, "50", phone="06 12 34 56 78")
        second = make_order(self.premium, "50", phone="+212612345678")
        award_points_for_order(first)
        award_points_for_order(second)
        self.assertEqual(LoyaltyWallet.objects.count(), 1)
        self.assertEqual(self.wallet_of(self.premium).balance, 10)


class DeliveredTransitionIntegrationTests(TestCase):
    """الربح كيوقع من view تبديل الحالة — مرة وحدة مهما تكرر الطلب."""

    def setUp(self):
        self.restaurant = make_restaurant("premium-view", "premium")
        self.owner = get_user_model().objects.create_user(
            username="premium-owner", **{"password": "premium-owner-pass-42"}
        )
        Membership.objects.create(
            user=self.owner,
            restaurant=self.restaurant,
            role=Membership.Roles.OWNER,
        )
        self.client.force_login(self.owner)
        self.order = make_order(
            self.restaurant, "55", status=Order.Status.READY
        )

    def deliver(self):
        return self.client.post(
            reverse(
                "orders:owner_order_status",
                args=[self.restaurant.slug, self.order.id],
            ),
            {"status": Order.Status.DELIVERED},
        )

    def test_delivery_via_view_awards_once(self):
        response = self.deliver()
        self.assertEqual(response.status_code, 302)
        wallet = LoyaltyWallet.objects.get(restaurant=self.restaurant)
        self.assertEqual(wallet.balance, 5)
        # محاولة ثانية: الانتقال ممنوع (Delivered نهائية) والرصيد ما كيتبدلش
        self.deliver()
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 5)
        self.assertEqual(
            LoyaltyTransaction.objects.filter(order=self.order).count(), 1
        )

    def test_pro_restaurant_delivery_via_view_awards_nothing(self):
        pro = make_restaurant("pro-view", "pro")
        pro_owner = get_user_model().objects.create_user(
            username="pro-owner", **{"password": "pro-owner-pass-4242"}
        )
        Membership.objects.create(
            user=pro_owner, restaurant=pro, role=Membership.Roles.OWNER
        )
        self.client.force_login(pro_owner)
        order = make_order(pro, "500", status=Order.Status.READY)
        self.client.post(
            reverse("orders:owner_order_status", args=[pro.slug, order.id]),
            {"status": Order.Status.DELIVERED},
        )
        self.assertFalse(LoyaltyWallet.objects.filter(restaurant=pro).exists())
