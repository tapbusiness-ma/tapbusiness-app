from django.conf import settings
from django.db import models


class Restaurant(models.Model):
    """مطعم واحد فالمنصة (tenant)."""

    name = models.CharField("الاسم", max_length=200)
    slug = models.SlugField(
        "الرابط",
        max_length=200,
        unique=True,
        help_text="يستعمل فرابط المطعم، مثال: kebab-house",
    )
    phone = models.CharField("الهاتف", max_length=20, blank=True)
    address = models.CharField("العنوان", max_length=255, blank=True)
    delivery_fee = models.DecimalField(
        "مصاريف التوصيل (درهم)", max_digits=8, decimal_places=2, default=0
    )
    is_active = models.BooleanField("نشط", default=True)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)

    class Meta:
        verbose_name = "مطعم"
        verbose_name_plural = "المطاعم"

    def __str__(self):
        return self.name


class Membership(models.Model):
    """ربط مستخدم بمطعم مع دور معين."""

    class Roles(models.TextChoices):
        OWNER = "owner", "مالك"
        MANAGER = "manager", "مدير"
        STAFF = "staff", "موظف"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="المستخدم",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="المطعم",
    )
    role = models.CharField(
        "الدور", max_length=20, choices=Roles.choices, default=Roles.STAFF
    )
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)

    class Meta:
        verbose_name = "عضوية"
        verbose_name_plural = "العضويات"
        unique_together = ("user", "restaurant")

    def __str__(self):
        return f"{self.user} — {self.restaurant} ({self.get_role_display()})"