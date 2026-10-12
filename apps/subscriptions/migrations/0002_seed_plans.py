from django.db import migrations


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "Plan")
    plans = [
        {
            "name": "Démo",
            "slug": "demo",
            "price_monthly": 0,
            "max_products": 10,
            "max_tables": 2,
            "description": "تجربة مجانية",
        },
        {
            "name": "Pro",
            "slug": "pro",
            "price_monthly": 199,
            "max_products": 0,
            "max_tables": 0,
            "description": "Menu complet FR/AR, QR tables, modifications illimitées",
        },
        {
            "name": "Premium",
            "slug": "premium",
            "price_monthly": 399,
            "max_products": 0,
            "max_tables": 0,
            "description": "Tout Pro + design sur-mesure + Google Business Profile + support prioritaire",
        },
    ]
    for plan in plans:
        Plan.objects.get_or_create(slug=plan["slug"], defaults=plan)


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plans, migrations.RunPython.noop),
    ]
