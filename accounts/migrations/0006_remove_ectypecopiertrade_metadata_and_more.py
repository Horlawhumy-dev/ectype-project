# Generated by Django 4.2.4 on 2023-11-04 09:53

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_remove_ectypecopiertrade_trade_sync_copier_ids_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ectypecopiertrade",
            name="metadata",
        ),
        migrations.AlterField(
            model_name="ectypetradeaccount",
            name="created_at",
            field=models.DateTimeField(
                default=datetime.datetime(2023, 11, 4, 10, 53, 29, 572130)
            ),
        ),
        migrations.AlterField(
            model_name="ectypetradeaccountcopier",
            name="created_at",
            field=models.DateTimeField(
                default=datetime.datetime(2023, 11, 4, 10, 53, 29, 573285)
            ),
        ),
    ]
