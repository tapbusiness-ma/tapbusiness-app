from django.contrib import admin

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


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "restaurant", "role", "created_at")
    list_filter = ("role",)