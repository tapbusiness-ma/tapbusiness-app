from django.db import models

from apps.restaurants.models import Restaurant


class Category(models.Model):
    """تصنيف فالمنيو (مثال: طاكوس، بيتزا)."""

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="المطعم",
    )
    name = models.CharField("الاسم", max_length=200)
    name_ar = models.CharField("الاسم بالعربية", max_length=200, blank=True)
    order = models.PositiveIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("نشط", default=True)

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.restaurant.name} — {self.name}"


class Product(models.Model):
    """طبق فالمنيو."""

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="المطعم",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="التصنيف",
    )
    name = models.CharField("الاسم", max_length=200)
    name_ar = models.CharField("الاسم بالعربية", max_length=200, blank=True)
    description = models.TextField("الوصف", blank=True)
    image = models.ImageField("الصورة", upload_to="products/", blank=True, null=True)
    price = models.DecimalField("الثمن (درهم)", max_digits=8, decimal_places=2)
    is_available = models.BooleanField("متوفر", default=True)
    order = models.PositiveIntegerField("الترتيب", default=0)
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)

    class Meta:
        verbose_name = "طبق"
        verbose_name_plural = "الأطباق"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} ({self.price} DH)"


class Modifier(models.Model):
    """إضافة اختيارية لطبق (مثال: جبن إضافي +5 درهم)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="modifiers",
        verbose_name="الطبق",
    )
    name = models.CharField("الاسم", max_length=200)
    price = models.DecimalField(
        "الثمن الإضافي (درهم)", max_digits=8, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = "إضافة"
        verbose_name_plural = "الإضافات"

    def __str__(self):
        return f"{self.product.name} + {self.name} ({self.price} DH)"