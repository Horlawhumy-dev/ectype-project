from enum import Enum


class PlatformFeatures(Enum):
    daily_withdrawal = "daily_withdrawal"
    weekly_transaction = "weekly_transaction"
    account_slot = "account_slot"
    email_notification = "email_notification"
    manage_account = "manage_account"
    max_trading_volume = "max_trading_volume"

    @classmethod
    def get_schema(cls, choice):
        schema = {
            cls.daily_withdrawal.value: {
                "type": "object",
                "title": cls.daily_withdrawal.name.replace("_", " "),
                "properties": {
                    "value": {
                        "type": "number",
                        "default": 0,
                    },
                },
            },
            cls.weekly_transaction.value: {
                "type": "object",
                "title": cls.weekly_transaction.name.replace("_", " "),
                "properties": {
                    "value": {
                        "type": "number",
                        "default": 0,
                    },
                },
            },
            cls.account_slot.value: {
                "type": "object",
                "title": cls.account_slot.name.replace("_", " "),
                "properties": {
                    "value": {
                        "type": "number",
                        "default": 0,
                    },
                },
            },
            cls.email_notification.value: {
                "type": "object",
                "title": cls.email_notification.name.replace("_", " "),
                "properties": {
                    "value": {
                        "type": "boolean",
                        "default": True,
                    },
                },
            },
            cls.manage_account.value: {
                "type": "object",
                "title": cls.manage_account.name.replace("_", " "),
                "properties": {
                    "value": {
                        "type": "boolean",
                        "default": True,
                    },
                },
            },
            cls.max_trading_volume.value: {
                "type": "object",
                "title": cls.max_trading_volume.name.replace("_", " "),
                "properties": {
                    "value": {
                        "type": "number",
                        "default": 0,
                    },
                },
            },
        }
        return schema.get(choice.value, {"additionalProperties": True})
