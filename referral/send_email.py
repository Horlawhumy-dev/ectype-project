import logging
from smtplib import SMTPException
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail

from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_referral_withdraw_email(email, receiver, subject):
    email_from = email
    html_message = render_to_string(
        "referral/referral_withdraw.html",
        {
            "receiver": receiver.capitalize()
        },
    )
    plain_message = strip_tags(html_message)
    recipient_list = [settings.EMAIL_HOST_USER, "phaceenginnering@gmail.com"]
    try:
        send_mail(
            subject,
            plain_message,
            email_from,
            recipient_list,
            fail_silently=False,
            html_message=html_message,
        )
        logging.info(f"{receiver}'s referral payout email sent at {datetime.now()}")

    except SMTPException as e:
        logging.debug(e)

    