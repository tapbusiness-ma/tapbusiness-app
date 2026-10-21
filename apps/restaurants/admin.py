from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry

from .models import Membership, Restaurant


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "phone")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]
    actions = ("activate_restaurants", "suspend_restaurants")

    @admin.action(description="✅ تفعيل (موافقة مالك المنصة)")
    def activate_restaurants(self, request, queryset):
        """تفعيل صريح من مالك المنصة — كيتسجل فـLogEntry (شكون، إمتى)."""
        LogEntry.objects.log_actions(
            request.user.pk, queryset, CHANGE, "تفعيل المطعم — موافقة مالك المنصة"
        )
        updated = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {updated} مطعم.")

    @admin.action(description="⏸ تعليق المطاعم")
    def suspend_restaurants(self, request, queryset):
        """تعليق كيوقف المنيو العمومي والطلبات وعمليات المالك فنفس اللحظة."""
        LogEntry.objects.log_actions(
            request.user.pk, queryset, CHANGE, "تعليق المطعم من مالك المنصة"
        )
        updated = queryset.update(is_active=False)
        self.message_user(request, f"تم تعليق {updated} مطعم.")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "restaurant", "role", "created_at")
    list_filter = ("role",)