import logging
import threading
from datetime import datetime
from smtplib import SMTPException

from .utils import send_invoice_mail, send_charge_otp

# Apply locks to avoid race conditions and ensures thread safety
invoice_email_lock = threading.Lock()
charge_otp_lock = threading.Lock()

class SendSubscriptionInvoiceEmailThread(threading.Thread):
    """Using Separate thread to send invoice email"""

    def __init__(self, data):
        self.data = data
        threading.Thread.__init__(self)

    def run(self):
        with invoice_email_lock:
            response = send_invoice_mail(self.data, "invoice.html")
            if response:
                logging.info(f"Subscription invoice email delivered successfully to {self.data.get('sender')} at {datetime.now()}")
            else:
                logging.info(f"Subscription invoice email not delivered to {self.data.get('sender')} at {datetime.now()}")


class SendChargeOTPThread(threading.Thread):
    """Using Separate thread to send OTP email"""

    def __init__(self, customer):
        self.customer = customer
        threading.Thread.__init__(self)

    def run(self):
        with charge_otp_lock:
            response = send_charge_otp(self.customer)
            if response.status_code not in [201, 200]:
                logging.info(f"{response.json()['message']} at {datetime.now()}")
            else:
                logging.info(
                    f"Email service for charge otp delivered to {self.customer['name']} around {datetime.now()}"
                )