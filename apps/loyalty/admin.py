from django.contrib import admin

from .models import LoyaltyTransaction, LoyaltyWallet


@admin.register(LoyaltyWallet)
class LoyaltyWalletAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "phone", "balance", "created_at")
    list_filter = ("restaurant",)
    search_fields = ("phone",)
    readonly_fields = ("token", "balance", "created_at", "updated_at")


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    """الدفتر للاطلاع فقط — الحركات كتخلق من الخدمة، ماشي يدوياً من الأدمن."""

    list_display = ("wallet", "kind", "points", "order", "created_at")
    list_filter = ("kind", "wallet__restaurant")
    readonly_fields = (
        "wallet",
        "kind",
        "points",
        "order",
        "reason",
        "created_by",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
