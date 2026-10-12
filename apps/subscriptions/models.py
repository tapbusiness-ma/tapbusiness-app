from django.db import models

from apps.restaurants.models import Restaurant


class Plan(models.Model):
    """باقة اشتراك (Démo / Pro / Premium)."""

    name = models.CharField("الاسم", max_length=100)
    slug = models.SlugField("الرمز", unique=True)
    price_monthly = models.DecimalField(
        "الثمن الشهري (درهم)", max_digits=8, decimal_places=2
    )
    max_products = models.PositiveIntegerField(
        "أقصى عدد الأطباق", default=0, help_text="0 = غير محدود"
    )
    max_tables = models.PositiveIntegerField(
        "أقصى عدد الطاولات", default=0, help_text="0 = غير محدود"
    )
    description = models.TextField("الوصف", blank=True)

    class Meta:
        verbose_name = "باقة"
        verbose_name_plural = "الباقات"

    def __str__(self):
        return f"{self.name} ({self.price_monthly} DH/mois)"


class Subscription(models.Model):
    """اشتراك مطعم فباقة معينة."""

    class Status(models.TextChoices):
        TRIAL = "trial", "تجريبي"
        ACTIVE = "active", "نشط"
        PAST_DUE = "past_due", "متأخر الدفع"
        CANCELLED = "cancelled", "ملغي"

    restaurant = models.OneToOneField(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name="المطعم",
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, verbose_name="الباقة")
    status = models.CharField(
        "الحالة", max_length=20, choices=Status.choices, default=Status.TRIAL
    )
    started_at = models.DateTimeField("تاريخ البداية", auto_now_add=True)
    ends_at = models.DateField("تاريخ النهاية", null=True, blank=True)
    notes = models.TextField("ملاحظات إدارية", blank=True)

    class Meta:
        verbose_name = "اشتراك"
        verbose_name_plural = "الاشتراكات"

    def __str__(self):
        return (
            f"{self.restaurant.name} — {self.plan.name} "
            f"({self.get_status_display()})"
        )
