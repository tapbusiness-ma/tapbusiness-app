"""خريطة روابط TAPBusiness — كل رابط كيرتبط بـview."""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    # روابط التطبيق (القوائم، الطلبات...) غنزيدوها فالمراحل الجاية
]
