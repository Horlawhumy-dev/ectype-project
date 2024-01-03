import bcrypt
from rest_framework.response import Response


# def check_account(querysets, request):
#     for account in querysets:
#         if int(account.account_number) == int(request.data["account_number"]):
#             return True
#     return False


def get_hashed_password_for(password, salt_rounds=12):
    """
    Args:
        password (str): The password to be hashed.
        salt_rounds (int): The number of salt rounds (default is 12).

    Returns:
        str: The hashed password as a string.
    """
    # Generate a salt and hash the password
    salt = bcrypt.gensalt(salt_rounds)
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    # Convert the binary hash to a UTF-8 encoded string
    return hashed_password.decode("utf-8")


def verify_password(hashed_password, password):
    """
    Args:
        hashed_password (str): The hashed password stored in the database.
        password (str): The user-provided password to be verified.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


class APIResponse:
    """API Response Format"""

    @staticmethod
    def send(message="", status_code=200, error="", data=None, count=None):
        # Ensure data is a hashable type (e.g., a dictionary)
        if data is None:
            return Response(
            {
                "message": message,
                "status_code": status_code,
                "error": error
            })

        if count is not None:
            return Response(
                {
                    "message": message,
                    "status_code": status_code,
                    "count": count,
                    "data": data,
                    "error": error
                }
            )

        return Response(
            {
                "message": message,
                "status_code": status_code,
                "data": data,
                "error": error
            }
        )