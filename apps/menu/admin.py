from django.contrib import admin

from .models import Category, Modifier, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "order", "is_active")
    list_filter = ("restaurant", "is_active")
    search_fields = ("name", "name_ar")
    list_editable = ("order", "is_active")


class ModifierInline(admin.TabularInline):
    model = Modifier
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "category", "price", "is_available")
    list_filter = ("restaurant", "category", "is_available")
    search_fields = ("name", "name_ar")
    list_editable = ("price", "is_available")
    inlines = [ModifierInline]