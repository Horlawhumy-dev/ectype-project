from django.contrib.auth.models import AbstractUser
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    EmailField,
    ForeignKey,
    GenericIPAddressField,
    JSONField,
)
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ectype_bend_beta.model_utils import BaseModelMixin
from users.managers import UserManager
from django.db.models import Sum


def default_user_metadata():
    return {
        "2fa": False,
        "email_notification": False,
        "email_updates": False,
    }


class User(AbstractUser):
    """
    Default custom user model for Ectype Project.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = CharField(max_length=100, blank=True, null=True)
    last_name = CharField(max_length=100, blank=True, null=True)
    email = EmailField(_("email address"), unique=True)
    address = CharField(max_length=100, blank=True, null=True)
    country = CharField(max_length=100, blank=True, null=True)
    token = CharField(max_length=100, blank=True, null=True)
    referred_by = EmailField(_("Referrer Email"), blank=True, null=True)
    metadata = JSONField(default=default_user_metadata, blank=True, null=True)
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})

    @property
    def current_subscription(self):
        from payment.models import Subscription

        now = timezone.now()
        active_subscription = Subscription.objects.filter(
            user=self, next_subscription_datetime__gte=now
        )
        return active_subscription

    @property
    def has_active_subscription(self):
        return True if self.current_subscription.count() >= 1 else False

    @property
    def permissions(self):
        if self.has_active_subscription:
            subscription = self.current_subscription
            features = subscription.features
            return features
        else:
            return []

    @property
    def total_slots(self):
        """
            Return the total number of slots the user has
        """
        account_slot = 0
        for subscription in self.current_subscription:
            features = subscription.features
            perm = features[0] #features list
            if perm.get("uid") == "account_slot":
                account_slot += int(perm.get("data", {}).get("value", 0))
        return account_slot

    @property
    def used_slots(self):
        """
        return the number of slots used by the user.
        """
        from accounts.models import EctypeTradeAccount

        trading_accounts_count = EctypeTradeAccount.objects.filter(user=self).count()
        return trading_accounts_count

    @property
    def free_slots(self):
        return self.total_slots - self.used_slots


class UserLoginRecord(BaseModelMixin):
    user = ForeignKey(User, on_delete=CASCADE)
    device_type = CharField(max_length=100)
    ip_address = GenericIPAddressField()
    login_success = BooleanField(default=False)
    login_time = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} logged in via {self.device_type}"
