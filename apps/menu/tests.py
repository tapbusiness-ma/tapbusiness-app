from django.test import TestCase
from django.urls import reverse

from apps.restaurants.models import Restaurant
from .models import Category, Product


class PublicMenuTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name="Test Resto", slug="test-resto",
            is_active=True,
        )
        self.category = Category.objects.create(
            restaurant=self.restaurant, name="Tacos"
        )

    def test_public_menu_shows_available_products_without_login(self):
        Product.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name="Chicken Tacos",
            price="35.00",
        )
        Product.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name="Unavailable Tacos",
            price="45.00",
            is_available=False,
        )

        response = self.client.get(
            reverse("menu:public_menu", args=[self.restaurant.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chicken Tacos")
        self.assertNotContains(response, "Unavailable Tacos")

    def test_menu_is_not_available_for_inactive_restaurant(self):
        self.restaurant.is_active = False
        self.restaurant.save(update_fields=["is_active"])

        response = self.client.get(
            reverse("menu:public_menu", args=[self.restaurant.slug])
        )

        self.assertEqual(response.status_code, 404)

    def test_qr_download_is_png_for_public_menu_url(self):
        response = self.client.get(
            reverse("menu:menu_qr", args=[self.restaurant.slug]),
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn('filename="qr-test-resto.png"', response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"\x89PNG\r\n\x1a\n"))