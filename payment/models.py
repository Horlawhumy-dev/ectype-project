from datetime import datetime
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import models  # noqa
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ectype_bend_beta.model_utils import BaseModelMixin
from payment.managers import BillingManager
from users.models import User

stripe.api_key = settings.STRIPE_SECRET_KEY


class Plan(BaseModelMixin):
    CURRENCY = (
        ("USD", "USD"),
        ("NGN", "NGN"),
    )
    BILLING_INTERVAL = (
        ("monthly", "monthly"),
        ("yearly", "yearly"),
    )
    name = models.CharField(max_length=100, verbose_name="Plan Name")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=20, choices=CURRENCY, default=CURRENCY[0][0], blank=True
    )
    billing_interval = models.CharField(
        max_length=100,
        choices=BILLING_INTERVAL,
        blank=True,
        default=BILLING_INTERVAL[0][0],
    )
    features = models.JSONField(blank=True, null=True, default=list)
    """
    [
        {
           "name": "Slot",
           "uid": "slot",
           "on": True,
        }
    ]
    """

    @property
    def duration(self) -> str:
        return "Month" if self.billing_interval == "monthly" else "Year"

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["price"]


class Receipt(BaseModelMixin):
    STATUS = (
        ("PENDING", "PENDING"),
        ("EXPIRED", "EXPIRED"),
        ("CANCELLED", "CANCELLED"),
        ("SUCCESSFUL", "SUCCESSFUL"),
    )
    plan = models.ForeignKey(
        "payment.Plan", on_delete=models.SET_NULL, null=True, related_name="receipts"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, blank=True, related_name="receipts"
    )
    vat = models.FloatField(blank=True, null=True, default=0.0)
    status = models.CharField(
        max_length=100, choices=STATUS, blank=True, default=STATUS[0][0]
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    @property
    def amount_to_pay(self):
        return self.price + (Decimal(self.vat or 0) * self.price)

    @property
    def plan_name(self):
        if self.plan:
            return self.plan.name
        
    def __str__(self): 
        return self.plan_name or str(self.amount_to_pay)


class Billing(Receipt):
    objects = BillingManager()

    class Meta:
        proxy = True


class Subscription(BaseModelMixin):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, blank=True, related_name="subscriptions"
    )
    plan: Plan = models.ForeignKey(
        "payment.Plan",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subscriptions",
    )
    next_plan = models.ForeignKey(
        "payment.Plan",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="post_subscriptions",
    )
    last_subscription_datetime = models.DateTimeField(default=timezone.now, blank=True)
    next_subscription_datetime = models.DateTimeField(blank=True, null=True)
    receipt: Receipt = models.ForeignKey(
        "payment.Receipt",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subscriptions",
    )

    @property
    def status(self):
        now = timezone.now()
        if self.next_subscription_datetime >= now:
            return "ACTIVE"
        else:
            return "EXPIRED"

    @property
    def features(self):
        if self.plan:
            return self.plan.features
        return []

    @property
    def start_date(self):
        return self.last_subscription_datetime

    @property
    def end_date(self):
        return self.next_subscription_datetime

    @property
    def price(self):
        return self.receipt.price

    @property
    def invoice_data(self) -> dict:
        """
        return the data for subscrition needed to generate an invoice.
        """
        data = {
            "subject": "Ectype Plan Subscription",
            "plan_name": self.plan.name,
            "email": self.user.email,
            "sender": self.user.first_name
        }
        return data

    def set_next_subscription_datetime(self) -> datetime:
        """
        Use the calendar to determine the exact datetime of the next subscription datetime.
        """
        from dateutil.relativedelta import relativedelta

        start_date = self.last_subscription_datetime or timezone.now()
        billing_interval = self.plan.billing_interval
        # match billing_interval:
        #     case "monthly":
        #         end_date = start_date + relativedelta(months=1)
        #     case "yearly":
        #         end_date = start_date + relativedelta(years=1)
        #     case _:
        #         end_date = None

        # python3.8 does not support above
        if billing_interval == "monthly" or billing_interval in [30, 31]:
            end_date = start_date + relativedelta(months=1)
        elif billing_interval == "yearly" or billing_interval in [365, 366]:
            end_date = start_date + relativedelta(years=1)
        else:
            end_date = None
        return end_date

    def save(self, *args, **kwargs):
        if not self.next_subscription_datetime:
            self.next_subscription_datetime = self.set_next_subscription_datetime()
        if not self.next_plan:
            self.next_plan = self.plan
        super().save(*args, **kwargs)


class Card(BaseModelMixin):
    """
    Card Model represents a Bank Card to be used for payment.
    The bank (confidential) details are stored on stripe and managed
    from the platform with specific key relationships.

    A Card object must have a user reference and an optional account reference.
    A Card object without an account reference is only useful for payment to be done before
    an account reference is created or made available. Once such payment is completed, the card
    is mostly inaccessible to the user/account excepted explicitly added the account afterwards.

    ### Attributes:
        - user (fk): User instance that owns the card
        - account (fk):  Account instance that owns the card
        - is_default (bool): Indicates whether the card is the default card for the user/account
        - metadata (dict): Key-Value pair of metadata returned by Stripe

    ### Properties:
        - name (str): the name on the card.
        - brand(str): the brand of the card.
        - funding(str): the funding type of the card.
        - last_4_digits(str): the last 4 of the card number.
        - expiry_date (datetime): the datetime aware expiration date of the card.
        - days_until_expiry (int):
        - stripe_customer_id (str):

    ### Features:
        - [X] Save the response of the created stripe card to the metadata fields.
        - [X] Prevent Multiple Card with same details for the same Account.
        - [X] Once deleted!, delete the corresponding stripe card object.
        - [X] Prevent Direct deletion of Default card by the User.
    """

    user = models.ForeignKey(
        "users.User",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    is_default = models.BooleanField(
        default=False,
        blank=True,
        help_text="Specifies if this is the default card for payment of the account",
    )
    metadata = models.JSONField(
        verbose_name=_("metadata"),
        blank=True,
        default=dict,
        help_text="Store more data on the card object",
    )

    @property
    def name(self) -> str or None:
        """
        returns the name on the card or None.
        """
        return self.metadata.get("name")

    @property
    def brand(self) -> str or None:
        """
        returns the brand of the card or Unknown.
        """
        return self.metadata.get("brand", "Unknown")

    @property
    def funding(self) -> str or None:
        """
        returns the funding type of the card or None.
        """
        return self.metadata.get("funding")

    @property
    def last_4_digits(self) -> str or None:
        """
        returns the last 4 digits of the card or None.
        """
        return self.metadata.get("last4")

    @property
    def expiry_date(self) -> datetime or None:
        """
        return the timezone-aware expiration date of the card or None.
        """
        expiry_month = self.metadata.get("exp_month")
        expiry_year = self.metadata.get("exp_year")
        timezone_obj = timezone.get_current_timezone()
        if not all((expiry_year, expiry_month)):
            return None
        return timezone.datetime(expiry_year, expiry_month, 1, tzinfo=timezone_obj)

    @property
    def days_until_expiry(self) -> int:
        """
        return the days until expiration of the card.

        This defaults to -1 if the expiry date can not be
        calculated.
        """
        if not self.expiry_date:
            return 0
        return (self.expiry_date - timezone.now()).days

    @property
    def stripe_customer_id(self) -> str:
        """
        returns the customer id linked to the card.
        """
        return self.metadata.get("customer", "")

    @classmethod
    def create_stripe_customer(cls, user: User = None):
        """
        Create and Return a New Stripe Customer Object.
        """
        name = getattr(user, "username", "no-name")
        try:
            new_customer = stripe.Customer.create(
                name=name,
                description=f"Stripe Customer Account For account with username: {name}",
            )

        # TODO: replace with more sensible stripe error class
        # except stripe.error.APIConnectionError as err:
        except Exception as err:
            error_message = err.json_body or err._message
            error_message = str(error_message)
            raise ValueError(error_message)
        if user:
            user.metadata["stripe_customer_id"] = new_customer.id
            user.save(update_fields=["metadata"])
        return new_customer

    @classmethod
    def retrieve_stripe_customer(cls, stripe_customer_id: str):
        """
        Retrieve a Stripe Customer Object with the stripe_custumer_id.
        """
        try:
            print("Retrieving an Exisiting Customer")
            customer = stripe.Customer.retrieve(stripe_customer_id)
        # TODO: replace with more sensible stripe error class
        except Exception as err:
            print("FAILED to retrieve customer")
            raise err
        return customer

    @classmethod
    def create_stripe_card(cls, stripe_customer_id: str, card_token):
        """
        create and return a stripe card object.
        """
        stripe_card = stripe.Customer.create_source(
            stripe_customer_id.encode("utf-8"),
            source=card_token,
        )
        return stripe_card

    @classmethod
    def create_card(
        cls,
        token: str,
        user: User,
        save_card=False,
        **kwargs,
    ):
        """
        Create a new Card instance associated with the given user and Stripe card details.
        """
        # try to get stripe_customer_id from the the metadata attribute of the current account or user

        stripe_customer_id = user.metadata.get("stripe_customer_id")
        if not stripe_customer_id:
            customer = cls.create_stripe_customer(user)
            stripe_customer_id = customer.id
        else:
            customer = cls.retrieve_stripe_customer(stripe_customer_id)

        try:
            # Create a Stripe card using the token above
            stripe_card = cls.create_stripe_card(
                stripe_customer_id,
                token,
            )

        except stripe.error.CardError as e:
            error_message = e.json_body or e._message
            error_message = str(error_message)
            raise ValueError(error_message)

        # Create a bank card instance with the Stripe card as the metadata
        if save_card:
            bank_card = cls.objects.create(
                id=stripe_card.id,
                user=user,
                metadata=stripe_card,
                **kwargs,
            )
            return bank_card
        else:
            card_data = {
                "id": stripe_card.id,
                "name": stripe_card.name,
                "brand": stripe_card.brand,
                "funding": stripe_card.funding,
                "last_4_digits": stripe_card.last4,
            }
            return card_data

    def save(self, *args, **kwargs) -> None:
        """
        if the current saved card is set to is_default is True.
        set all other cards by the same account is_default to false
        """
        if self.is_default is True:
            linked_cards = Card.objects.filter(account=self.account)
            if self.id:
                linked_cards = linked_cards.exclude(id=self.id)
            linked_cards.update(is_default=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        """
        Deletes a card from a Stripe customer.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            None.

        Raises:
            ValueError: If the card is the default card.
            stripe.error.CardError: If the card could not be deleted from Stripe.
        """
        # Check if the card is the default card.
        if self.is_default:
            raise ValueError(
                "Can not delete the default card, change default card first"
            )
        # Try to delete the card from Stripe.
        try:
            deleted_card = stripe.Customer.delete_source(
                self.stripe_customer_id,
                self.id,
            )
            print("Deleted stripe Card = ", deleted_card)
        except stripe.error.CardError as e:
            raise ValueError(
                f"Can not proceed with deleting card \
                             since, stripe reference was not deleted, Error={e}"
            )
        else:
            print("about to delete platform card reference")
            super().delete(*args, **kwargs)

    class Meta:
        ordering = ["-is_default"]  # in descending order from True (1) to False (0).
