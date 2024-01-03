from datetime import datetime
import uuid
from django.db import models

account_type_choices = (("UNKNOWN", "UNKNOWN"), ("4", "MT4"), ("5", "MT5"))

account_risk_type_choices = (
    ("risk_multiplier_by_balance", "Risk Multiplier By Balance"),
    ("risk_multiplier_by_equity", "Risk Multiplier By Equity"),
    ("risk_amount_per_trade", "Risk Multiplier By Trade"),
    ("lot_multiplier", "Lot Multiplier"),
    ("fixed_lot", "Fixed Lot"),
    ("percentage_risk_per_trade_by_balance", "Percentage Risk Per Trade By Balance"),
    ("percentage_risk_per_trade_by_equity", "Percentage Risk Per Trade By Equity")
)
account_copier_mode_choices = (("off", "Off"), ("on", "On"), ("monitor", "Monitor"))


def get_default_metadata():
    return {}


def generate_id(length: int = 10):
    return uuid.uuid4().hex[:length]


class EctypeTradeAccount(models.Model):
    id = models.CharField(
        primary_key=True, default=generate_id, editable=False, max_length=255
    )
    user = models.ForeignKey(
        "users.User", related_name="trading_account", on_delete=models.CASCADE
    )
    tradesync_account_id = models.CharField(max_length=150)
    account_name = models.CharField(max_length=250)
    account_type = models.CharField(
        max_length=150, choices=account_type_choices, default=account_type_choices[0][0]
    )
    account_number = models.CharField(max_length=250)
    account_password = models.CharField(max_length=250)
    broker_name = models.CharField(max_length=150)
    broker_server = models.CharField(max_length=250)
    metadata = models.JSONField(default=get_default_metadata, blank=True, null=True)
    models
    created_at = models.DateTimeField(default=datetime.now())
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.account_number
    

class EctypeCopierTrade(models.Model):
    id = models.CharField(
        primary_key=True, default=generate_id, editable=False, max_length=255
    )
    user = models.ForeignKey(
        "users.User",
        related_name="copier_trades",
        on_delete=models.CASCADE
    )
    lead_id = models.CharField(max_length=150)
    risk_multiplier = models.CharField(max_length=150)
    risk_type = models.CharField(
        max_length=150,
        choices=account_risk_type_choices,
        default=account_risk_type_choices[0][0],
    )
    mode = models.CharField(
        max_length=50,
        choices=account_copier_mode_choices,
        default=account_copier_mode_choices[0][0],
    )
    follower_ids = models.JSONField(default=dict)
    metadata = models.JSONField(default=get_default_metadata, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id