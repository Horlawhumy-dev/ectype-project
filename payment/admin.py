from django.contrib import admin  # noqa

from payment.forms import PlanForm
from payment.models import Billing, Card, Plan, Receipt, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    form = PlanForm
    list_display = ["name", "price", "billing_interval"]


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "amount_to_pay", "status"]


@admin.register(Card)
class CardAdminn(admin.ModelAdmin):
    list_display = ["user", "brand", "funding", "last_4_digits"]


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "amount_to_pay"]


@admin.register(Subscription)
class SubscriptioAdmin(admin.ModelAdmin):
    list_display = ["user", "status", "plan", "start_date", "end_date"]
