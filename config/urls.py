"""خريطة روابط TAPBusiness — كل رابط كيرتبط بـview."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.accounts import views as accounts_views

urlpatterns = [
    path("", accounts_views.home, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("restaurants/", include("apps.restaurants.urls")),
    path("", include("apps.tables.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.menu.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
