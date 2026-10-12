from django.contrib import admin

from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "restaurant", "is_active")
    list_filter = ("restaurant", "is_active")
    search_fields = ("number",)
    readonly_fields = ("qr_token",)
