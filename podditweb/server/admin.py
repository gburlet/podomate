from django.contrib import admin
from server.models import PodditUser, License, Product, Activation, AppVersion


@admin.register(PodditUser)
class PodditUserAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'price')


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'key', 'issued_date')
    search_fields = ('user__username', 'product__sku',)
    raw_id_fields = ('user',)


@admin.register(Activation)
class ActivationAdmin(admin.ModelAdmin):
    list_display = ('license_key', 'product_sku', 'mac', 'activation_date')
    search_fields = ('license__key', 'license__product__sku',)
    raw_id_fields = ('license',)

    def license_key(self, obj):
        return obj.license.key

    def product_sku(self, obj):
        return obj.license.product.sku


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ('product', 'version', 'release_date', 'sunset_date')
