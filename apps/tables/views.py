import io

import qrcode
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse

from apps.restaurants.models import Membership, Restaurant
from .forms import TableForm
from .models import Table


def table_menu(request, slug, token):
    """سكانا QR ديال الطاولة → نحفظو رقمها فالsession ونحولوه للمنيو."""
    table = get_object_or_404(
        Table,
        restaurant__slug=slug,
        qr_token=token,
        is_active=True,
        restaurant__is_active=True,
    )
    request.session[f"table_{table.restaurant.id}"] = table.number
    return redirect("menu:public_menu", slug=slug)


@login_required
def table_qr(request, slug, table_id):
    """تحميل QR code ديال طاولة (للطباعة) — غير لمول المطعم."""
    restaurant = _get_owned_restaurant(request, slug)
    table = get_object_or_404(
        Table,
        id=table_id,
        restaurant=restaurant,
        is_active=True,
    )
    table_url = request.build_absolute_uri(
        reverse("tables:table_menu", args=[slug, table.qr_token])
    )
    image = qrcode.make(table_url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Content-Disposition"] = (
        f'attachment; filename="qr-table-{table.number}.png"'
    )
    return response
def _get_owned_restaurant(request, slug):
    """يرجع المطعم إلا كان المستخدم مالك أو مدير ديالو، وإلا 404."""
    return get_object_or_404(
        Restaurant.objects.filter(
            slug=slug,
            is_active=True,
            memberships__user=request.user,
            memberships__role__in=[
                Membership.Roles.OWNER,
                Membership.Roles.MANAGER,
            ],
        )
    )


@login_required
def owner_tables(request, slug):
    """إدارة الطاولات ديال مول المطعم."""
    restaurant = _get_owned_restaurant(request, slug)
    ctx = {
        "restaurant": restaurant,
        "tables": restaurant.tables.all(),
        "form": TableForm(),
        "memberships": request.user.memberships.select_related(
            "restaurant"
        ).order_by("restaurant__name"),
    }
    return render(request, "tables/owner_tables.html", ctx)


@login_required
@require_POST
def owner_table_add(request, slug):
    restaurant = _get_owned_restaurant(request, slug)
    form = TableForm(request.POST)
    form.instance.restaurant = restaurant
    number = (request.POST.get("number") or "").strip()
    duplicate = bool(number) and Table.objects.filter(
        restaurant=restaurant, number=number
    ).exists()
    if form.is_valid() and not duplicate:
        form.save()
        return redirect("tables:owner_tables", slug=slug)
    if duplicate:
        form.add_error("number", "هاد الرقم مستعمل — ختار رقم آخر.")
    ctx = {
        "restaurant": restaurant,
        "tables": restaurant.tables.all(),
        "form": form,
        "memberships": request.user.memberships.select_related(
            "restaurant"
        ).order_by("restaurant__name"),
    }
    return render(request, "tables/owner_tables.html", ctx)


@login_required
@require_POST
def owner_table_delete(request, slug, table_id):
    restaurant = _get_owned_restaurant(request, slug)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    table.delete()
    return redirect("tables:owner_tables", slug=slug)


@login_required
@require_POST
def owner_table_toggle(request, slug, table_id):
    restaurant = _get_owned_restaurant(request, slug)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    table.is_active = not table.is_active
    table.save(update_fields=["is_active"])
    return redirect("tables:owner_tables", slug=slug)
