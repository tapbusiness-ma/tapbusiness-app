import secrets

from django.db import models

from apps.restaurants.models import Restaurant


def generate_token():
    return secrets.token_urlsafe(8)


class Table(models.Model):
    """طاولة فمطعم — عندها رمز سري للـQR."""

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="tables",
        verbose_name="المطعم",
    )
    number = models.CharField("رقم الطاولة", max_length=20)
    qr_token = models.CharField(
        "رمز QR", max_length=32, unique=True, default=generate_token
    )
    is_active = models.BooleanField("نشطة", default=True)

    class Meta:
        verbose_name = "طاولة"
        verbose_name_plural = "الطاولات"
        unique_together = ("restaurant", "number")

    def __str__(self):
        return f"{self.restaurant.name} — طاولة {self.number}"
