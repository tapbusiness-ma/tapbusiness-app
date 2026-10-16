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
    path("dashboard/<slug:slug>/tables/", views.owner_tables, name="owner_tables"),
    path(
        "dashboard/<slug:slug>/tables/add/",
        views.owner_table_add,
        name="owner_table_add",
    ),
    path(
        "dashboard/<slug:slug>/tables/<int:table_id>/delete/",
        views.owner_table_delete,
        name="owner_table_delete",
    ),
    path(
        "dashboard/<slug:slug>/tables/<int:table_id>/toggle/",
        views.owner_table_toggle,
        name="owner_table_toggle",
    ),
]
