from django.contrib import admin

from .models import  ReferralToken, ReferralPayment


@admin.register(ReferralToken)
class ReferralTokenAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "token", "active", "updated_at"]
    list_display_links = ["id"]


@admin.register(ReferralPayment)
class ReferralPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "cash_out", "unpaid_referrals", "updated_at"]
    list_display_links = ["id"]