from django.contrib import admin
from .models import EctypeBroker, EctypeBrokerServer


@admin.register(EctypeBroker)
class EctypeBrokerAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "mt_version"]
    list_display_links = ["id"]


@admin.register(EctypeBrokerServer)
class EctypeBrokerServerAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "mt_version"]
    list_display_links = ["id"]
