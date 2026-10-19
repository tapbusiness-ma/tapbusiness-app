import secrets

from django.db import models

from apps.menu.models import Product
from apps.restaurants.models import Restaurant


def generate_token():
    """رمز عشوائي آمن لرابط تأكيد الطلب."""
    return secrets.token_urlsafe(32)


class Order(models.Model):
    """طلب واحد من زبون."""

    class Status(models.TextChoices):
        PENDING = "pending", "قيد الانتظار"
        CONFIRMED = "confirmed", "مؤكد"
        PREPARING = "preparing", "قيد التحضير"
        READY = "ready", "جاهز"
        DELIVERED = "delivered", "تم التوصيل"
        CANCELLED = "cancelled", "ملغي"

    class OrderType(models.TextChoices):
        DELIVERY = "delivery", "توصيل"
        TABLE = "table", "طاولة"

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="المطعم",
    )
    order_type = models.CharField(
        "النوع", max_length=20, choices=OrderType.choices, default=OrderType.DELIVERY
    )
    status = models.CharField(
        "الحالة", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    customer_name = models.CharField("اسم الزبون", max_length=200)
    customer_phone = models.CharField("هاتف الزبون", max_length=20)
    address = models.CharField("العنوان", max_length=255, blank=True)
    table_number = models.CharField("رقم الطاولة", max_length=20, blank=True)
    subtotal = models.DecimalField(
        "المجموع الفرعي", max_digits=10, decimal_places=2, default=0
    )
    delivery_fee = models.DecimalField(
        "مصاريف التوصيل", max_digits=8, decimal_places=2, default=0
    )
    total = models.DecimalField(
        "المجموع", max_digits=10, decimal_places=2, default=0
    )
    created_at = models.DateTimeField("تاريخ الطلب", auto_now_add=True)
    token = models.CharField(
        "رمز التأكيد", max_length=64, unique=True, default=generate_token
    )

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"طلب #{self.id} — {self.restaurant.name} ({self.total} DH)"

    # مسار الحالات المسموح: خطي، والإلغاء ممكن من أي مرحلة قبل التوصيل
    ALLOWED_TRANSITIONS = {
        Status.PENDING: {Status.CONFIRMED, Status.CANCELLED},
        Status.CONFIRMED: {Status.PREPARING, Status.CANCELLED},
        Status.PREPARING: {Status.READY, Status.CANCELLED},
        Status.READY: {Status.DELIVERED, Status.CANCELLED},
        Status.DELIVERED: set(),
        Status.CANCELLED: set(),
    }

    def can_transition_to(self, new_status):
        """واش الانتقال من الحالة الحالية للحالة الجديدة مسموح؟"""
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())

    def get_allowed_transitions(self):
        """لائحة (value, label) ديال الحالات المسموح الانتقال ليها."""
        return [
            (s.value, s.label)
            for s in self.Status
            if self.can_transition_to(s.value)
        ]


class OrderItem(models.Model):
    """سطر فالطلب — نسخة من الثمن وقت التأكيد (snapshot)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="الطلب",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="الطبق",
    )
    product_name = models.CharField("اسم الطبق (وقت الطلب)", max_length=200)
    unit_price = models.DecimalField(
        "ثمن الوحدة (وقت الطلب)", max_digits=8, decimal_places=2
    )
    quantity = models.PositiveIntegerField("الكمية", default=1)

    class Meta:
        verbose_name = "سطر طلب"
        verbose_name_plural = "سطور الطلبات"

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"