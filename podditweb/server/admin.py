from django.contrib import admin
from server.models import PodditUser, License, Product


@admin.register(PodditUser)
class PodditUserAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'price')


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'key')
    search_fields = ('user__username', 'product__sku',)
    raw_id_fields = ('user',)
