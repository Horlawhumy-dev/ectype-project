import logging
import threading
from smtplib import SMTPException

from .send_email import send_account_add_email, send_account_copy_email

# Apply locks to avoid race conditions and ensures thread safety
add_or_copy_lock = threading.Lock()

class SendTradeAccountEmailThread(threading.Thread):
    """Using Separate thread to send account and copy emails"""

    def __init__(self, data):
        self.data = data
        threading.Thread.__init__(self)

    def run(self):
        try:
            with add_or_copy_lock:
                if self.data.get("type") == "add":
                    send_account_add_email(self.data)
                if self.data.get("type") == "copy":
                    send_account_copy_email(self.data)
        except SMTPException as e:
            logging.debug("There was an error sending an email. " + str(e))

