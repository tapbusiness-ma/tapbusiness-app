from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.restaurants.models import Membership, Restaurant


class AccountsViewsTests(TestCase):
    def test_signup_creates_user_and_logs_them_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new-owner",
                "password1": "tap-user-password-42",
                "password2": "tap-user-password-42",
            },
        )

        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.assertTrue(
            get_user_model().objects.filter(username="new-owner").exists()
        )
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}",
        )

    def test_dashboard_shows_only_current_users_restaurants(self):
        user = get_user_model().objects.create_user(username="member")
        other_user = get_user_model().objects.create_user(username="other")
        visible_restaurant = Restaurant.objects.create(name="Visible", slug="visible")
        hidden_restaurant = Restaurant.objects.create(name="Hidden", slug="hidden")
        Membership.objects.create(user=user, restaurant=visible_restaurant)
        Membership.objects.create(user=other_user, restaurant=hidden_restaurant)
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertContains(response, "Visible")
        self.assertNotContains(response, "Hidden")


class LoginLockoutTests(TestCase):
    """حماية django-axes: بعد 5 محاولات فاشلة، حتى كلمة السر الصحيحة تتحظر."""

    def setUp(self):
        get_user_model().objects.create_user(
            username="victim", **{"password": "correct-password-42"}
        )
        self.login_url = reverse("accounts:login")

    def test_lockout_after_five_failed_attempts(self):
        for _ in range(5):
            self.client.post(
                self.login_url, {"username": "victim", "password": "wrong-pass"}
            )

        # المحاولة السادسة بكلمة سر صحيحة: خاصها تتحظر
        response = self.client.post(
            self.login_url,
            {"username": "victim", "password": "correct-password-42"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_normal_login_still_works(self):
        response = self.client.post(
            self.login_url,
            {"username": "victim", "password": "correct-password-42"},
        )
        self.assertRedirects(
            response,
            reverse("accounts:dashboard"),
            fetch_redirect_response=False,
        )
        self.assertIn("_auth_user_id", self.client.session)
