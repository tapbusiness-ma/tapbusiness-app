from django.urls import path

from . import views

app_name = "tables"

urlpatterns = [
    path("m/<slug:slug>/t/<str:token>/", views.table_menu, name="table_menu"),
    path(
        "m/<slug:slug>/tables/<int:table_id>/qr/",
        views.table_qr,
        name="table_qr",
    ),
]
