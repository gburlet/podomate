from django.contrib import admin
from server.models import PodditUser


@admin.register(PodditUser)
class PodditUserAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)
