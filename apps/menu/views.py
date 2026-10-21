import io

import qrcode
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from apps.restaurants.models import Membership, Restaurant
from .forms import CategoryForm, ProductForm
from .models import Category, Product


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
    table_number = request.session.get(f"table_{restaurant.id}", "")
    return render(
        request,
        "menu/public_menu.html",
        {
            "restaurant": restaurant,
            "categories": categories,
            "table_number": table_number,
        },
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
def _get_member_restaurant(request, slug):
    """يرجع المطعم (أي حالة) إلا كان المستخدم مالك أو مدير ديالو، وإلا 404."""
    return get_object_or_404(
        Restaurant.objects.filter(
            slug=slug,
            memberships__user=request.user,
            memberships__role__in=[
                Membership.Roles.OWNER,
                Membership.Roles.MANAGER,
            ],
        )
    )


def _owner_nav(request):
    return {
        "memberships": request.user.memberships.select_related(
            "restaurant"
        ).order_by("restaurant__name")
    }


@login_required
def owner_menu(request, slug):
    """إدارة المنيو ديال مول المطعم: التصنيفات والأطباق."""
    restaurant = _get_member_restaurant(request, slug)
    categories = restaurant.categories.prefetch_related("products").all()
    ctx = {
        "restaurant": restaurant,
        "categories": categories,
        "category_form": CategoryForm(),
    }
    ctx.update(_owner_nav(request))
    return render(request, "menu/owner_menu.html", ctx)


@login_required
@require_POST
def owner_category_add(request, slug):
    restaurant = _get_member_restaurant(request, slug)
    form = CategoryForm(request.POST)
    if form.is_valid():
        category = form.save(commit=False)
        category.restaurant = restaurant
        category.save()
    return redirect("menu:owner_menu", slug=slug)


@login_required
@require_POST
def owner_category_delete(request, slug, category_id):
    restaurant = _get_member_restaurant(request, slug)
    category = get_object_or_404(Category, id=category_id, restaurant=restaurant)
    category.delete()
    return redirect("menu:owner_menu", slug=slug)


@login_required
def owner_product_add(request, slug):
    restaurant = _get_member_restaurant(request, slug)
    if request.method == "POST":
        form = ProductForm(restaurant, request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.restaurant = restaurant
            product.save()
            return redirect("menu:owner_menu", slug=slug)
    else:
        form = ProductForm(restaurant)
    ctx = {"restaurant": restaurant, "form": form, "title": "🍽 طبق جديد"}
    ctx.update(_owner_nav(request))
    return render(request, "menu/product_form.html", ctx)


@login_required
def owner_product_edit(request, slug, product_id):
    restaurant = _get_member_restaurant(request, slug)
    product = get_object_or_404(Product, id=product_id, restaurant=restaurant)
    if request.method == "POST":
        form = ProductForm(restaurant, request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("menu:owner_menu", slug=slug)
    else:
        form = ProductForm(restaurant, instance=product)
    ctx = {"restaurant": restaurant, "form": form, "title": f"تعديل: {product.name}"}
    ctx.update(_owner_nav(request))
    return render(request, "menu/product_form.html", ctx)


@login_required
@require_POST
def owner_product_delete(request, slug, product_id):
    restaurant = _get_member_restaurant(request, slug)
    product = get_object_or_404(Product, id=product_id, restaurant=restaurant)
    product.delete()
    return redirect("menu:owner_menu", slug=slug)


@login_required
@require_POST
def owner_product_toggle(request, slug, product_id):
    """إظهار/إخفاء طبق بسرعة — بلا ما تمسح."""
    restaurant = _get_member_restaurant(request, slug)
    product = get_object_or_404(Product, id=product_id, restaurant=restaurant)
    product.is_available = not product.is_available
    product.save(update_fields=["is_available"])
    return redirect("menu:owner_menu", slug=slug)
