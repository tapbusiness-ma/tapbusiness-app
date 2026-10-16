from django.urls import path

from . import views

app_name = "restaurants"

urlpatterns = [
    path("create/", views.restaurant_create, name="create"),
]