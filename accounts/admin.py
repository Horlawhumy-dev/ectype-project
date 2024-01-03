from django.contrib import admin

from .models import EctypeTradeAccount, EctypeCopierTrade


@admin.register(EctypeTradeAccount)
class TradingAccountAdmin(admin.ModelAdmin):
    list_display = ["id", "account_name", "account_type", "created_at"]
    list_display_links = ["id", "account_name"]

@admin.register(EctypeCopierTrade)
class EctypeCopierAdmin(admin.ModelAdmin):
    list_display = ["id", "lead_id", "created_at"]
    list_display_links = ["id", "lead_id"]