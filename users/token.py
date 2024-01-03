import base64

# import operator
from datetime import datetime

import pyotp
from django.conf import settings

from users.models import User

# from django.contrib.auth.tokens import default_token_generator # noqa # WHY THE IMPORT HERE
# from django.utils.crypto import constant_time_compare, salted_hmac
# from django.utils.http import base36_to_int, int_to_base36


class TokenGenerator:
    """
    Strategy object used to generate and check tokens for the password
    reset mechanism.
    """

    key_salt = "django.contrib.auth.tokens.PasswordResetTokenGenerator"
    algorithm = None
    _secret = None

    def __init__(self):
        self.algorithm = self.algorithm or "sha256"

    def _get_secret(self):
        return self._secret or settings.SECRET_KEY

    def _set_secret(self, secret):
        self._secret = secret

    secret = property(_get_secret, _set_secret)

    def make_token(self, user):
        """
        Return a token that can be used once to do a password reset
        for the given user.
        """
        return self._make_token_with_timestamp(user, self._num_seconds(self._now()))

    def check_token(self, user, token):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_part, otp = token[: len(token) // 2], token[len(token) // 2 :]
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        hash_val = base64.b32encode(self._make_hash_value(user, ts_part).encode())
        OTP = pyotp.HOTP(hash_val, digits=3)
        if OTP.verify(int(otp), int(ts_part)):
            return True
        # if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
        #     return False

        # Check the timestamp is within limit.
        # if (self._num_seconds(self._now()) - ts) > settings.PASSWORD_RESET_TIMEOUT:
        #     return False

        return False

    def _make_token_with_timestamp(self, user: User, timestamp):
        # timestamp is number of seconds since 2001-1-1. Converted to base 36,
        # this gives us a 6 digit string until about 2069.
        ts_part = self._get_timestamp_digits(str(timestamp))
        key = base64.b32encode(
            self._make_hash_value(user, ts_part).encode()
        )  # Key is generated
        OTP = pyotp.HOTP(key, digits=3)  # HOTP Model for OTP is created
        # Using Multi-Threading send the OTP Using Messaging Services like Twilio or Fast2sms
        otp = OTP.at(ts_part)
        return f"{ts_part}{otp}"

    def _make_hash_value(self, user, timestamp):
        """
        Hash the user's primary key, email (if available), and some user state
        that's sure to change after a password reset to produce a token that is
        invalidated when it's used:
        1. The password field will change upon a password reset (even if the
           same password is chosen, due to password salting).
        2. The last_login field will usually be updated very shortly after
           a password reset.
        Failing those things, settings.PASSWORD_RESET_TIMEOUT eventually
        invalidates the token.

        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.
        """
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        login_timestamp = (
            ""
            if user.last_login is None
            else user.last_login.replace(microsecond=0, tzinfo=None)
        )
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, "") or ""
        return f"{user.pk}{user.password}{login_timestamp}{timestamp}{email}"

    def _get_timestamp_digits(self, timestamp) -> str:
        return int(timestamp[-3:])

    def _num_seconds(self, dt):
        return int((dt - datetime(2001, 1, 1)).total_seconds())

    def _now(self):
        # Used for mocking in tests
        return datetime.now()


default_token_generator = TokenGenerator()
