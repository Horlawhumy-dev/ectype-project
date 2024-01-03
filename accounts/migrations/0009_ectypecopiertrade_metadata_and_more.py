# Generated by Django 4.2.4 on 2023-12-06 10:46

import accounts.models
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_alter_ectypetradeaccount_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="ectypecopiertrade",
            name="metadata",
            field=models.JSONField(
                blank=True, default=accounts.models.get_default_metadata, null=True
            ),
        ),
        migrations.AlterField(
            model_name="ectypetradeaccount",
            name="created_at",
            field=models.DateTimeField(
                default=datetime.datetime(2023, 12, 6, 11, 46, 20, 745518)
            ),
        ),
    ]
