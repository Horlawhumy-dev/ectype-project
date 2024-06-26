# Generated by Django 4.2.4 on 2023-10-14 15:27

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import ectype_bend_beta.model_utils


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Card",
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
                (
                    "is_default",
                    models.BooleanField(
                        blank=True,
                        default=False,
                        help_text="Specifies if this is the default card for payment of the account",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Store more data on the card object",
                        verbose_name="metadata",
                    ),
                ),
            ],
            options={
                "ordering": ["-is_default"],
            },
        ),
        migrations.CreateModel(
            name="Plan",
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
                ("name", models.CharField(max_length=100, verbose_name="Plan Name")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "currency",
                    models.CharField(
                        blank=True,
                        choices=[("USD", "USD"), ("NGN", "NGN")],
                        default="USD",
                        max_length=20,
                    ),
                ),
                (
                    "billing_interval",
                    models.CharField(
                        blank=True,
                        choices=[("monthly", "monthly"), ("yearly", "yearly")],
                        default="monthly",
                        max_length=100,
                    ),
                ),
                ("features", models.JSONField(blank=True, default=list, null=True)),
            ],
            options={
                "ordering": ["price"],
            },
        ),
        migrations.CreateModel(
            name="Receipt",
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
                ("vat", models.FloatField(blank=True, default=0.0, null=True)),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PENDING", "PENDING"),
                            ("EXPIRED", "EXPIRED"),
                            ("CANCELLED", "CANCELLED"),
                            ("SUCCESSFUL", "SUCCESSFUL"),
                        ],
                        default="PENDING",
                        max_length=100,
                    ),
                ),
                (
                    "price",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Subscription",
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
                (
                    "last_subscription_datetime",
                    models.DateTimeField(blank=True, default=django.utils.timezone.now),
                ),
                (
                    "next_subscription_datetime",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "next_plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="post_subscriptions",
                        to="payment.plan",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subscriptions",
                        to="payment.plan",
                    ),
                ),
                (
                    "receipt",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subscriptions",
                        to="payment.receipt",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
                "abstract": False,
            },
        ),
    ]
