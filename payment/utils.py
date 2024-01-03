import logging
from datetime import datetime
from smtplib import SMTPException
from ectype_bend_beta import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .wave import Flutterwave


def send_invoice_mail(data: dict, email_template: str) -> bool:
    subject = data.get("subject")
    from_email = settings.EMAIL_HOST_USER
    sender = data.get("sender")
    email = data.get("email")
    plan_name = data.get("plan_name")
    expiry_date = data.get("expiry_date")
    recipient_list = [email]

    html_content = render_to_string(f"payment/{email_template}", {
        "sender_name": sender, "plan_name": plan_name, 
        "expiry_date": expiry_date
    })
    text_content = strip_tags(html_content)

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logging.info(f"Delivered subscription email to {sender} around {datetime.now()}")
    except SMTPException as e:
        logging.debug("There was an error sending an email. " + str(e))
        return False

    return True

def send_charge_otp(customer):
    flutterwave = Flutterwave()
    data = {
        "length": 6,
        "customer": customer,
        "sender": "Ectype",
        "send": True,
        "medium": [
            "email",
            "whatsapp"
        ],
        "expiry": 5
    }
    try:
        response = flutterwave.generate_otp(data)
        logging.info(f"{response.json()['message']} at {datetime.now()}")
    except Exception as e:
        logging.debug("There was an error sending an email. " + str(e))

    return response