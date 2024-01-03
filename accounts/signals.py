import logging
from datetime import datetime

from django.db.models import Q
from django.db.models.signals import post_delete, post_save  # noqa
from django.dispatch import receiver

from accounts.models import EctypeTradeAccount, EctypeCopierTrade

from notification.models import Notification

@receiver(post_delete, sender=EctypeTradeAccount)
def delete_account_copier_for(sender, instance, **kwargs):
    # this is only triggered if the deleted account is a lead to a copier instance
    trading_copier_instance = None
    try:
        trading_copier_instance = EctypeCopierTrade.objects.get(lead_id=instance.id)
    except EctypeCopierTrade.DoesNotExist as err:
        logging.debug(err)

    if trading_copier_instance is not None:
        trading_copier_instance.delete()

        logging.info(
            f"Trading Account Copier is deleted successfully around {datetime.now()}"
        )

        Notification.objects.create(
            user=instance.user, message=f"Trading Account copy deleted successfully"
        )