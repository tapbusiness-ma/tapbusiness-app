from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("m/<slug:slug>/cart/", views.cart_detail, name="cart"),
    path("m/<slug:slug>/cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path(
        "m/<slug:slug>/cart/remove/<int:product_id>/",
        views.cart_remove,
        name="cart_remove",
    ),
    path("m/<slug:slug>/checkout/", views.checkout, name="checkout"),
    path(
        "m/<slug:slug>/order/<int:order_id>/ok/",
        views.order_success,
        name="order_success",
    ),
]
