"""رمز تأكيد آمن لكل طلب — حماية صفحة التأكيد."""

import secrets

import apps.orders.models
from django.db import migrations, models


def generate_token():
    return secrets.token_urlsafe(32)


def backfill_tokens(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    for order in Order.objects.filter(token__isnull=True):
        order.token = generate_token()
        order.save(update_fields=["token"])


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="token",
            field=models.CharField(
                max_length=64, null=True, blank=True, unique=True
            ),
        ),
        migrations.RunPython(backfill_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="token",
            field=models.CharField(
                max_length=64,
                unique=True,
                default=apps.orders.models.generate_token,
                verbose_name="رمز التأكيد",
            ),
        ),
    ]
