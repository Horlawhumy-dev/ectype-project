# Generated by Django 4.2.4 on 2023-10-26 14:30

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ectypetradeaccount",
            name="created_at",
            field=models.DateTimeField(
                default=datetime.datetime(2023, 10, 26, 15, 30, 22, 141519)
            ),
        ),
        migrations.AlterField(
            model_name="ectypetradeaccountcopier",
            name="created_at",
            field=models.DateTimeField(
                default=datetime.datetime(2023, 10, 26, 15, 30, 22, 142036)
            ),
        ),
    ]
