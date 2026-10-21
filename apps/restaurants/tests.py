from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from apps.menu.models import Category, Product
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
        self.assertRedirects(
            response, reverse("restaurant_pending", args=[restaurant.slug])
        )
        self.assertEqual(restaurant.slug, "ma-resto")
        # مطعم جديد كيبقى قيد المراجعة حتى يفعّلو مالك المنصة صراحة
        self.assertFalse(restaurant.is_active)
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

class OwnerApprovalAccessControlTests(TestCase):
    """متطلب تفعيل مالك المنصة: لا تفعيل ذاتي، لا صلاحيات ذاتية، الموافقة للأدمن فقط."""

    def setUp(self):
        User = get_user_model()
        self.platform_owner = User.objects.create_superuser(
            username="platform-owner",
            email="owner@example.com",
            **{"password": "platform-owner-pass-42"},
        )
        self.owner_a = User.objects.create_user(
            username="owner-a", **{"password": "owner-a-pass-42"}
        )
        self.owner_b = User.objects.create_user(
            username="owner-b", **{"password": "owner-b-pass-42"}
        )
        # مطعم قيد المراجعة (الافتراضي الجديد: غير نشط)
        self.pending = Restaurant.objects.create(
            name="Pending Resto", slug="pending-resto"
        )
        Membership.objects.create(
            user=self.owner_a,
            restaurant=self.pending,
            role=Membership.Roles.OWNER,
        )
        # مطعم مفعّل ديال مالك آخر
        self.active = Restaurant.objects.create(
            name="Active Resto", slug="active-resto", is_active=True
        )
        Membership.objects.create(
            user=self.owner_b,
            restaurant=self.active,
            role=Membership.Roles.OWNER,
        )
        self.category = Category.objects.create(
            restaurant=self.pending, name="Tacos"
        )
        self.product = Product.objects.create(
            restaurant=self.pending,
            category=self.category,
            name="Tacos Poulet",
            price="35.00",
        )

    def test_signup_never_grants_staff_or_superuser(self):
        self.client.post(
            reverse("accounts:signup"),
            {
                "username": "sneaky",
                "password1": "sneaky-pass-4242",
                "password2": "sneaky-pass-4242",
                "is_staff": "on",
                "is_superuser": "on",
            },
        )
        user = get_user_model().objects.get(username="sneaky")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_restaurant_cannot_self_activate(self):
        self.client.force_login(self.owner_b)
        self.client.post(
            reverse("restaurants:create"),
            {
                "name": "Sneaky Resto",
                "slug": "",
                "phone": "",
                "address": "",
                "delivery_fee": "0.00",
                "is_active": "on",
            },
        )
        resto = Restaurant.objects.get(name="Sneaky Resto")
        self.assertFalse(resto.is_active)

    def test_pending_restaurant_is_not_public(self):
        self.assertEqual(
            self.client.get(
                reverse("menu:public_menu", args=["pending-resto"])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                reverse("menu:menu_qr", args=["pending-resto"])
            ).status_code,
            404,
        )
        response = self.client.post(
            reverse("orders:cart_add", args=["pending-resto", self.product.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_pending_owner_can_prepare_menu_tables_settings(self):
        self.client.force_login(self.owner_a)
        self.assertEqual(
            self.client.get(
                reverse("menu:owner_menu", args=["pending-resto"])
            ).status_code,
            200,
        )
        response = self.client.post(
            reverse("menu:owner_category_add", args=["pending-resto"]),
            {"name": "Pizza", "order": "0"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Category.objects.filter(
                restaurant=self.pending, name="Pizza"
            ).exists()
        )
        self.assertEqual(
            self.client.get(
                reverse("tables:owner_tables", args=["pending-resto"])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("restaurant_settings", args=["pending-resto"])
            ).status_code,
            200,
        )

    def test_pending_owner_operations_redirect_to_pending_page(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("orders:owner_orders", args=["pending-resto"])
        )
        self.assertRedirects(
            response, reverse("restaurant_pending", args=["pending-resto"])
        )

    def test_pending_page_only_for_members(self):
        self.client.force_login(self.owner_a)
        self.assertEqual(
            self.client.get(
                reverse("restaurant_pending", args=["pending-resto"])
            ).status_code,
            200,
        )
        self.client.force_login(self.owner_b)
        self.assertEqual(
            self.client.get(
                reverse("restaurant_pending", args=["pending-resto"])
            ).status_code,
            404,
        )

    def test_settings_form_cannot_activate_restaurant(self):
        self.client.force_login(self.owner_a)
        self.client.post(
            reverse("restaurant_settings", args=["pending-resto"]),
            {
                "name": "Pending Resto",
                "phone": "",
                "address": "",
                "delivery_fee": "0.00",
                "is_active": "on",
            },
        )
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.is_active)

    def test_regular_user_cannot_approve_via_admin(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("admin:restaurants_restaurant_changelist"),
            {
                "action": "activate_restaurants",
                "_selected_action": [str(self.pending.pk)],
            },
        )
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.is_active)
        self.assertIn(response.status_code, (302, 403, 404))

    def test_staff_without_permission_cannot_approve(self):
        staff = get_user_model().objects.create_user(
            username="staff-noperm",
            is_staff=True,
            **{"password": "staff-pass-4242"},
        )
        self.client.force_login(staff)
        self.client.post(
            reverse("admin:restaurants_restaurant_changelist"),
            {
                "action": "activate_restaurants",
                "_selected_action": [str(self.pending.pk)],
            },
        )
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.is_active)

    def test_platform_owner_approval_activates_and_is_logged(self):
        self.client.force_login(self.platform_owner)
        self.client.post(
            reverse("admin:restaurants_restaurant_changelist"),
            {
                "action": "activate_restaurants",
                "_selected_action": [str(self.pending.pk)],
            },
        )
        self.pending.refresh_from_db()
        self.assertTrue(self.pending.is_active)
        entry = (
            LogEntry.objects.filter(
                content_type=ContentType.objects.get_for_model(Restaurant),
                object_id=str(self.pending.pk),
                user=self.platform_owner,
            )
            .order_by("-action_time")
            .first()
        )
        self.assertIsNotNone(entry)
        self.assertIn("تفعيل", entry.change_message)
        # من بعد التفعيل: المنيو العمومي كيولي متاح
        self.assertEqual(
            self.client.get(
                reverse("menu:public_menu", args=["pending-resto"])
            ).status_code,
            200,
        )

    def test_suspension_blocks_operations_and_public(self):
        self.client.force_login(self.platform_owner)
        self.client.post(
            reverse("admin:restaurants_restaurant_changelist"),
            {
                "action": "suspend_restaurants",
                "_selected_action": [str(self.active.pk)],
            },
        )
        self.active.refresh_from_db()
        self.assertFalse(self.active.is_active)
        self.client.force_login(self.owner_b)
        response = self.client.get(
            reverse("orders:owner_orders", args=["active-resto"])
        )
        self.assertRedirects(
            response, reverse("restaurant_pending", args=["active-resto"])
        )
        self.assertEqual(
            self.client.get(
                reverse("menu:public_menu", args=["active-resto"])
            ).status_code,
            404,
        )

    def test_cross_tenant_prep_isolation(self):
        self.client.force_login(self.owner_b)
        self.assertEqual(
            self.client.get(
                reverse("menu:owner_menu", args=["pending-resto"])
            ).status_code,
            404,
        )
        response = self.client.post(
            reverse("menu:owner_category_add", args=["pending-resto"]),
            {"name": "Hack", "order": "0"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Category.objects.filter(
                restaurant=self.pending, name="Hack"
            ).exists()
        )
