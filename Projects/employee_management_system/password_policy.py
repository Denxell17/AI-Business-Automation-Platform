"""Conservative password policy for ABAP account credentials."""

import unicodedata


MINIMUM_PASSWORD_LENGTH = 15
MAXIMUM_PASSWORD_LENGTH = 128

COMMON_PASSWORDS = frozenset(
    {
        "123456789012345",
        "admin123456789",
        "administrator",
        "changeme123456",
        "letmein12345678",
        "password123456",
        "password123456789",
        "qwerty123456789",
        "welcome12345678",
    }
)


def password_meets_policy(username: str, password: str) -> bool:
    """Return whether a proposed new password meets the local policy."""
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    if not MINIMUM_PASSWORD_LENGTH <= len(password) <= MAXIMUM_PASSWORD_LENGTH:
        return False
    if not password.strip():
        return False
    if any(unicodedata.category(character).startswith("C") for character in password):
        return False

    normalized_password = password.casefold()
    normalized_username = username.strip().casefold()
    if normalized_password in COMMON_PASSWORDS:
        return False
    if normalized_username:
        obvious_username_passwords = {
            normalized_username,
            f"{normalized_username}123",
            f"{normalized_username}123!",
            f"{normalized_username}password",
            f"{normalized_username}password123!",
        }
        if normalized_password in obvious_username_passwords:
            return False
    return True


def password_is_safe_to_verify(password: object) -> bool:
    """Bound untrusted login input before invoking the password KDF."""
    return isinstance(password, str) and len(password) <= MAXIMUM_PASSWORD_LENGTH
