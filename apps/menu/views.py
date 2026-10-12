import io

import qrcode
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.restaurants.models import Restaurant
from .models import Product


def public_menu(request, slug):
    """صفحة المنيو العمومية ديال مطعم (بلا دخول)."""
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    categories = restaurant.categories.filter(is_active=True).prefetch_related(
        Prefetch(
            "products",
            queryset=Product.objects.filter(
                restaurant=restaurant, is_available=True
            ),
        )
    )
    return render(
        request,
        "menu/public_menu.html",
        {"restaurant": restaurant, "categories": categories},
    )


def menu_qr(request, slug):
    """توليد QR code ديال رابط المنيو (تحميل PNG)."""
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    menu_url = request.build_absolute_uri(
        reverse("menu:public_menu", args=[restaurant.slug])
    )
    image = qrcode.make(menu_url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Content-Disposition"] = (
        f'attachment; filename="qr-{restaurant.slug}.png"'
    )
    return response