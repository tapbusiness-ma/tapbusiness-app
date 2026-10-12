from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.restaurants.models import Membership, Restaurant
from .models import Plan, Subscription


class SubscriptionTests(TestCase):
    def test_seed_migration_creates_all_plans(self):
        self.assertEqual(
            set(Plan.objects.values_list("slug", flat=True)),
            {"demo", "pro", "premium"},
        )
        self.assertEqual(Plan.objects.get(slug="pro").price_monthly, Decimal("199.00"))
        self.assertEqual(Plan.objects.get(slug="demo").max_products, 10)
        self.assertEqual(Plan.objects.get(slug="demo").max_tables, 2)

    def test_dashboard_shows_subscription_and_missing_subscription(self):
        user = get_user_model().objects.create_user(username="restaurant-owner")
        subscribed = Restaurant.objects.create(name="Subscribed", slug="subscribed")
        unsubscribed = Restaurant.objects.create(name="Unsubscribed", slug="unsubscribed")
        Membership.objects.create(user=user, restaurant=subscribed)
        Membership.objects.create(user=user, restaurant=unsubscribed)
        Subscription.objects.create(
            restaurant=subscribed,
            plan=Plan.objects.get(slug="pro"),
            status=Subscription.Status.ACTIVE,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertContains(response, "Pro")
        self.assertContains(response, "نشط")
        self.assertContains(response, "بلا اشتراك")
