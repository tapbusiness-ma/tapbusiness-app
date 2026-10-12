import io

import qrcode
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

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


def table_qr(request, slug, table_id):
    """تحميل QR code ديال طاولة (للطباعة)."""
    table = get_object_or_404(
        Table,
        id=table_id,
        restaurant__slug=slug,
        restaurant__is_active=True,
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
