from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Address, Customer


class AddressInline(TabularInline):
    model = Address
    extra = 0


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ("full_name", "email", "phone", "user", "created_at")
    search_fields = ("full_name", "email", "phone", "user__username")
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ("full_name", "city", "state", "pincode", "customer", "is_default")
    search_fields = ("full_name", "phone", "pincode", "city")
    list_filter = ("state", "is_default")
