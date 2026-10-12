from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("m/<slug:slug>/", views.public_menu, name="public_menu"),
    path("m/<slug:slug>/qr/", views.menu_qr, name="menu_qr"),
]