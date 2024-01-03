import logging
import threading
from datetime import datetime
from smtplib import SMTPException

from .send_email import send_referral_withdraw_email
    
withdrawal_lock = threading.Lock()

class SendReferralPaymentWithdrawEMailThread(threading.Thread):
    """Using Separate thread to send referral withdrawal email"""
    def __init__(self, subject, email, user):
        self._email = email
        self._subject = subject
        self._user = user
        threading.Thread.__init__(self)

    def run(self):
        try:
            with withdrawal_lock:
                send_referral_withdraw_email(
                    email=self._email, receiver=self._user, subject=self._subject
                )
                
                logging.info(
                    f"Email service for referral payout delivered to {self._user} around {datetime.now()}"
                )
        except SMTPException as e:
            logging.debug("There was an error sending an email. " + str(e))
