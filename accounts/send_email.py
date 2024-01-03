import logging
from smtplib import SMTPException
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail

from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_account_copy_email(data):
    email_from = settings.EMAIL_HOST_USER
    html_message = render_to_string(
        "accounts/copy.html",
        {
            "receiver_name": data.get("receiver"),
        },
    )
    plain_message = strip_tags(html_message)
    recipient_list = [data.get("email")]
    try:
        send_mail(
            data.get("subject"),
            plain_message,
            email_from,
            recipient_list,
            fail_silently=False,
            html_message=html_message,
        )
        logging.info(f"{data.get('receiver')}'s trading account copy success email sent at {datetime.now()}")
    except SMTPException as e:
        logging.debug(e)


def send_account_add_email(data):
    email_from = settings.EMAIL_HOST_USER
    html_message = render_to_string(
        "accounts/add.html",
        {
            "receiver_name": data.get("receiver"),
        },
    )
    plain_message = strip_tags(html_message)
    recipient_list = [data.get("email")]
    try:
        send_mail(
            data.get("subject"),
            plain_message,
            email_from,
            recipient_list,
            fail_silently=False,
            html_message=html_message,
        )
        logging.info(f"{data.get('receiver')}'s trading account success email sent at {datetime.now()}")

    except SMTPException as e:
        logging.debug(e)