import hashlib


def generate_fever_key(email: str, password: str) -> str:
    """
    Generate an API key for the Fever API based on the user's email and password.

    Args:
        email (str): The user's email address.
        password (str): The user's password.

    Returns:
        str: The generated API key, which is an MD5 hash of the email and password
    """

    return hashlib.md5(f"{email}:{password}".encode()).hexdigest()
