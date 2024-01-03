# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def generate_generic_plan_data(apps, schema_editor):
    Plan = apps.get_model("payment", "Plan")

    plan_data = [
        {
            "name": "Duo",
            "price": 5.5,
            "billing_interval": "monthly",
            "features": [
                {
                    "on": True,
                    "uid": "account_slot",
                    "name": "Add 2 Trading Account",
                    "data": {"value": "2"},
                }
            ],
        },
        {
            "name": "Thrix",
            "price": 7.5,
            "billing_interval": "monthly",
            "features": [
                {
                    "on": True,
                    "uid": "account_slot",
                    "name": "Add 3 Trading Account",
                    "data": {"value": "3"},
                }
            ],
        },
        {
            "name": "Four",
            "price": 11.5,
            "billing_interval": "monthly",
            "features": [
                {
                    "on": True,
                    "uid": "account_slot",
                    "name": "Add 4 Trading Account",
                    "data": {"value": "4"},
                }
            ],
        },
        {
            "name": "Pent",
            "price": 15.5,
            "billing_interval": "monthly",
            "features": [
                {
                    "on": True,
                    "uid": "account_slot",
                    "name": "Add 5 Trading Account",
                    "data": {"value": "5"},
                }
            ],
        },
    ]

    for data in plan_data:
        plan, created = Plan.objects.get_or_create(**data)
        print(f"Plan: {plan}, Created: {created}")


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(generate_generic_plan_data),
    ]
