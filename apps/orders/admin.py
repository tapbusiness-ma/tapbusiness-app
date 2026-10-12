from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "restaurant",
        "customer_name",
        "customer_phone",
        "order_type",
        "status",
        "total",
        "created_at",
    )
    list_filter = ("restaurant", "status", "order_type")
    search_fields = ("customer_name", "customer_phone")
    list_editable = ("status",)
    readonly_fields = ("subtotal", "total", "created_at")
    inlines = [OrderItemInline]