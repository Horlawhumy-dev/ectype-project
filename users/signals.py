import logging
from datetime import datetime
from django.conf.settings import REFERRAL_AMOUNT_PER_HEAD
from django.dispatch import receiver


from django.db.models.signals import post_save, post_delete # noqa

from referral.models import ReferralPayment

from notification.models import Notification

from django.contrib.auth import get_user_model

User = get_user_model()



"""
    TODO: This signal below is failing, could be later reverted to in future.
"""
# @receiver(post_save, sender=User)
# def add_referral_for(sender, created, instance, **kwargs):
#     if created and instance.referred_by:
#         referral_pay_instance = None
#         referrer = None
#         try:
#             referral_pay_instance = ReferralPayment.objects.get(owner__email=instance.referred_by)
#         except ReferralPayment.DoesNotExist as err:
#             logging.debug(err)

#         if referral_pay_instance is not None:
#             referral_pay_instance.unpaid_referrals+=1
#             referral_pay_instance.save()


#         else:
#             referrer = User.objects.get(email=instance.referred_by)
#             ReferralPayment.objects.create(
#                 owner=referrer,
#                 unpaid_referrals=1
#             )

#         logging.info(
#             f"Referral is successfully added for {instance.referred_by} around {datetime.now()}"
#         )

#         Notification.objects.create(
#             user=referrer or referral_pay_instance.owner, message=f"You have successfully referred {instance.first_name} {instance.last_name}"
#         )



@receiver(post_delete, sender=User)
def delete_referral_for(sender, instance, **kwargs):
    referral_pay_instance = None
    try:
        referral_pay_instance = ReferralPayment.objects.get(owner__email=instance.referred_by)
    except ReferralPayment.DoesNotExist as err:
        logging.debug(err)

    if referral_pay_instance is not None:
        referral_pay_instance.unpaid_referrals-=1 if referral_pay_instance.unpaid_referrals else 0
        referral_pay_instance.paid_referrals-=1 if referral_pay_instance.paid_referrals else 0
        referral_pay_instance.cash_out = float(referral_pay_instance.cash_out) - ((REFERRAL_AMOUNT_PER_HEAD/100) * float(referral_pay_instance.cash_out)) if referral_pay_instance.cash_out else 0.00
        referral_pay_instance.save()

    logging.info(
        f"Referree account is successfully deleted around {datetime.now()}"
    )

    Notification.objects.create(
        user=referral_pay_instance.owner, message=f"Your referree {instance.first_name} {instance.last_name}'s account is deleted."
    )