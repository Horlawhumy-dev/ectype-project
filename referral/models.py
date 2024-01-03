from django.db import models
from ectype_bend_beta.model_utils import BaseModelMixin

# Create your models here.


class ReferralToken(BaseModelMixin):

    owner = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, blank=True, related_name="referraltoken"
    )

    token = models.CharField(max_length=255)


class ReferralPayment(BaseModelMixin):

    owner = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, blank=True, related_name="referralpaymant"
    )
    
    cash_out = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    paid_referrals = models.IntegerField(default=0)
    unpaid_referrals = models.IntegerField(default=0)
