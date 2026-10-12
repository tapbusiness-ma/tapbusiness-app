from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.menu.models import Product
from apps.restaurants.models import Restaurant
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
                order = Order.objects.create(
                    restaurant=restaurant,
                    customer_name=form.cleaned_data["customer_name"],
                    customer_phone=form.cleaned_data["customer_phone"],
                    address=form.cleaned_data["address"],
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
