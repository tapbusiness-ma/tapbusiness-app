from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.menu.models import Product
from apps.restaurants.models import Membership, Restaurant
from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem


def _get_restaurant(slug):
    return get_object_or_404(Restaurant, slug=slug, is_active=True)


@require_POST
def cart_add(request, slug, product_id):
    restaurant = _get_restaurant(slug)
    product = get_object_or_404(
        Product, id=product_id, restaurant=restaurant, is_available=True
    )
    Cart(request, restaurant).add(product.id)
    return redirect("orders:cart", slug=slug)


def cart_detail(request, slug):
    restaurant = _get_restaurant(slug)
    cart = Cart(request, restaurant)
    return render(
        request, "orders/cart.html", {"restaurant": restaurant, "cart": cart}
    )


@require_POST
def cart_remove(request, slug, product_id):
    restaurant = _get_restaurant(slug)
    Cart(request, restaurant).remove(product_id)
    return redirect("orders:cart", slug=slug)


def checkout(request, slug):
    restaurant = _get_restaurant(slug)
    cart = Cart(request, restaurant)
    lines = cart.lines()
    if not lines:
        return redirect("menu:public_menu", slug=slug)

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                subtotal = sum(
                    (line["product"].price * line["quantity"] for line in lines),
                    start=Decimal("0.00"),
                )
                delivery_fee = restaurant.delivery_fee
                table_number = request.session.get(f"table_{restaurant.id}", "")
                order = Order.objects.create(
                    restaurant=restaurant,
                    order_type=(
                        Order.OrderType.TABLE
                        if table_number
                        else Order.OrderType.DELIVERY
                    ),
                    customer_name=form.cleaned_data["customer_name"],
                    customer_phone=form.cleaned_data["customer_phone"],
                    address=form.cleaned_data["address"],
                    table_number=table_number,
                    subtotal=subtotal,
                    delivery_fee=delivery_fee,
                    total=subtotal + delivery_fee,
                )
                OrderItem.objects.bulk_create(
                    [
                        OrderItem(
                            order=order,
                            product=line["product"],
                            product_name=line["product"].name,
                            unit_price=line["product"].price,
                            quantity=line["quantity"],
                        )
                        for line in lines
                    ]
                )
            cart.clear()
            return redirect(
                "orders:order_success", slug=slug, order_id=order.id
            )
    else:
        form = CheckoutForm()

    return render(
        request,
        "orders/checkout.html",
        {"restaurant": restaurant, "cart": cart, "form": form},
    )


def order_success(request, slug, order_id):
    restaurant = _get_restaurant(slug)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    return render(
        request,
        "orders/success.html",
        {"restaurant": restaurant, "order": order},
    )
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
def owner_orders(request, slug):
    """لوحة الطلبات ديال مول المطعم: الإحصائيات + اللائحة + تغيير الحالة."""
    restaurant = _get_owned_restaurant(request, slug)
    status_filter = request.GET.get("status", "")
    orders = restaurant.orders.prefetch_related("items").order_by("-created_at")
    if status_filter in dict(Order.Status.choices):
        orders = orders.filter(status=status_filter)
    today = timezone.localdate()
    stats = {
        "pending_count": restaurant.orders.filter(
            status=Order.Status.PENDING
        ).count(),
        "today_count": restaurant.orders.filter(created_at__date=today).count(),
        "today_total": restaurant.orders.filter(
            created_at__date=today,
            status__in=[
                Order.Status.CONFIRMED,
                Order.Status.PREPARING,
                Order.Status.READY,
                Order.Status.DELIVERED,
            ],
        ).aggregate(total=Sum("total"))["total"]
        or 0,
    }
    memberships = request.user.memberships.select_related("restaurant").order_by(
        "restaurant__name"
    )
    return render(
        request,
        "orders/owner_orders.html",
        {
            "restaurant": restaurant,
            "orders": orders,
            "stats": stats,
            "status_filter": status_filter,
            "status_choices": Order.Status.choices,
            "memberships": memberships,
        },
    )


@login_required
@require_POST
def owner_order_status(request, slug, order_id):
    """تبديل حالة الطلب من طرف مول المطعم."""
    restaurant = _get_owned_restaurant(request, slug)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    new_status = request.POST.get("status")
    if new_status in dict(Order.Status.choices):
        order.status = new_status
        order.save(update_fields=["status"])
    return redirect("orders:owner_orders", slug=slug)
