from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.subscriptions.models import Plan, Subscription
from .models import Membership, Restaurant


class RestaurantCreateTests(TestCase):
    def test_create_restaurant_assigns_owner_and_demo_trial(self):
        user = get_user_model().objects.create_user(
            username="restaurant-owner", password="test-password"
        )
        demo_plan = Plan.objects.get(slug="demo")
        self.client.force_login(user)

        response = self.client.post(
            reverse("restaurants:create"),
            {
                "name": "Ma Resto",
                "slug": "",
                "phone": "",
                "address": "",
                "delivery_fee": "0.00",
            },
        )

        restaurant = Restaurant.objects.get(name="Ma Resto")
        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.assertEqual(restaurant.slug, "ma-resto")
        self.assertTrue(
            Membership.objects.filter(
                user=user,
                restaurant=restaurant,
                role=Membership.Roles.OWNER,
            ).exists()
        )
        subscription = Subscription.objects.get(restaurant=restaurant)
        self.assertEqual(subscription.plan, demo_plan)
        self.assertEqual(subscription.status, Subscription.Status.TRIAL)