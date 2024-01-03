import bcrypt

def get_referral_token_for(email, salt_rounds=12):
    """
    Args:
        email (str): The email to be hashed.
        salt_rounds (int): The number of salt rounds (default is 12).

    Returns:
        str: The hashed email as a string.
    """
    # Generate a salt and hash the email
    salt = bcrypt.gensalt(salt_rounds)
    hashed_email = bcrypt.hashpw(email.encode("utf-8"), salt)

    # Convert the binary hash to a UTF-8 encoded string
    return hashed_email.decode("utf-8")


def verify_referral_token_for(hashed_email, email):
    """
    Args:
        email (str): The hashed email stored in the database.
        email (str): The user email to be verified.

    Returns:
        bool: True if the email matches the hash, False otherwise.
    """
    return bcrypt.checkpw(email.encode("utf-8"), hashed_email.encode("utf-8"))
