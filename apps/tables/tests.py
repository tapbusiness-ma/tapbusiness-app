from django.test import TestCase
from django.urls import reverse

from apps.restaurants.models import Restaurant
from .models import Table


class TableQrTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(is_active=True,
            name="Table Resto", slug="table-resto"
        )
        self.table = Table.objects.create(restaurant=self.restaurant, number="T1")

    def test_table_qr_redirects_to_menu_and_sets_table_in_session(self):
        response = self.client.get(
            reverse(
                "tables:table_menu",
                args=[self.restaurant.slug, self.table.qr_token],
            )
        )

        self.assertRedirects(
            response, reverse("menu:public_menu", args=[self.restaurant.slug])
        )
        self.assertEqual(
            self.client.session[f"table_{self.restaurant.id}"], "T1"
        )
        menu_response = self.client.get(
            reverse("menu:public_menu", args=[self.restaurant.slug])
        )
        self.assertContains(menu_response, "طاولة T1")

    def test_inactive_table_qr_is_rejected(self):
        self.table.is_active = False
        self.table.save(update_fields=["is_active"])

        response = self.client.get(
            reverse(
                "tables:table_menu",
                args=[self.restaurant.slug, self.table.qr_token],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_table_qr_download_is_png(self):
        from django.contrib.auth.models import User

        from apps.restaurants.models import Membership

        # مجهول → تحويل لصفحة الدخول (تحميل الـQR خاص بمول المطعم)
        anon = self.client.get(
            reverse(
                "tables:table_qr",
                args=[self.restaurant.slug, self.table.id],
            )
        )
        self.assertEqual(anon.status_code, 302)

        user = User.objects.create_user("owner", password="x")
        Membership.objects.create(
            user=user,
            restaurant=self.restaurant,
            role=Membership.Roles.OWNER,
        )
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "tables:table_qr",
                args=[self.restaurant.slug, self.table.id],
            ),
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn('filename="qr-table-T1.png"', response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"\x89PNG\r\n\x1a\n"))
