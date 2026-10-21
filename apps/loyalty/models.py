import secrets

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.orders.models import Order
from apps.restaurants.models import Restaurant


def generate_wallet_token():
    """رمز سري خاص بمحفظة الزبون — مفتاح الوصول لصفحة المحفظة وصرف النقط."""
    return secrets.token_urlsafe(32)


class LoyaltyWallet(models.Model):
    """محفظة ولاء زبون واحد عند مطعم واحد — الأرصدة منفصلة بين المطاعم."""

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="loyalty_wallets",
        verbose_name="المطعم",
    )
    phone = models.CharField("هاتف الزبون (موحّد)", max_length=32)
    token = models.CharField(
        "رمز المحفظة السري",
        max_length=64,
        unique=True,
        default=generate_wallet_token,
    )
    balance = models.PositiveIntegerField("الرصيد الحالي (نقط)", default=0)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "محفظة ولاء"
        verbose_name_plural = "محافظ الولاء"
        constraints = [
            models.UniqueConstraint(
                fields=["restaurant", "phone"],
                name="unique_wallet_per_restaurant_phone",
            ),
        ]

    def __str__(self):
        return f"{self.restaurant.name} — {self.phone} ({self.balance} نقطة)"


class LoyaltyTransaction(models.Model):
    """حركة واحدة فدفتر الولاء — الرصيد ما كيتبدلش بلا حركة مسجلة."""

    class Kind(models.TextChoices):
        EARN = "earn", "ربح"
        REDEEM = "redeem", "صرف"
        ADJUST = "adjust", "تصحيح يدوي"

    wallet = models.ForeignKey(
        LoyaltyWallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="المحفظة",
    )
    kind = models.CharField("النوع", max_length=10, choices=Kind.choices)
    points = models.IntegerField("النقط (موقعة: + ربح / − صرف أو تصحيح)")
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loyalty_transactions",
        verbose_name="الطلب",
    )
    reason = models.CharField("السبب", max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loyalty_adjustments",
        verbose_name="المسؤول",
    )
    created_at = models.DateTimeField("التاريخ", auto_now_add=True)

    class Meta:
        verbose_name = "حركة ولاء"
        verbose_name_plural = "حركات الولاء"
        ordering = ["-created_at"]
        constraints = [
            # طلب واحد = ربح واحد، مهما تكررت المحاولات أو تقاطعت الطلبات
            models.UniqueConstraint(
                fields=["order"],
                condition=Q(kind="earn"),
                name="unique_earn_per_order",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.points} — {self.wallet.phone}"
