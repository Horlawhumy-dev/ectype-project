# Generated by Django 4.2.4 on 2023-11-30 11:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import ectype_bend_beta.model_utils


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReferralToken",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=ectype_bend_beta.model_utils.generate_id,
                        editable=False,
                        max_length=255,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "uid",
                    models.CharField(
                        default=ectype_bend_beta.model_utils.generate_id,
                        editable=False,
                        max_length=255,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "active",
                    models.BooleanField(
                        db_index=True, default=True, verbose_name="active"
                    ),
                ),
                ("token", models.CharField(max_length=255)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="referraltoken",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
                "abstract": False,
            },
        ),
    ]
