"""خريطة روابط TAPBusiness — كل رابط كيرتبط بـview."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
]
