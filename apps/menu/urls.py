from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("m/<slug:slug>/", views.public_menu, name="public_menu"),
    path("m/<slug:slug>/qr/", views.menu_qr, name="menu_qr"),
    path("dashboard/<slug:slug>/menu/", views.owner_menu, name="owner_menu"),
    path(
        "dashboard/<slug:slug>/menu/category/add/",
        views.owner_category_add,
        name="owner_category_add",
    ),
    path(
        "dashboard/<slug:slug>/menu/category/<int:category_id>/delete/",
        views.owner_category_delete,
        name="owner_category_delete",
    ),
    path(
        "dashboard/<slug:slug>/menu/product/add/",
        views.owner_product_add,
        name="owner_product_add",
    ),
    path(
        "dashboard/<slug:slug>/menu/product/<int:product_id>/edit/",
        views.owner_product_edit,
        name="owner_product_edit",
    ),
    path(
        "dashboard/<slug:slug>/menu/product/<int:product_id>/delete/",
        views.owner_product_delete,
        name="owner_product_delete",
    ),
    path(
        "dashboard/<slug:slug>/menu/product/<int:product_id>/toggle/",
        views.owner_product_toggle,
        name="owner_product_toggle",
    ),
]