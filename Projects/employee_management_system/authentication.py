import hashlib
import hmac
import secrets


HASH_NAME = "sha256"
HASH_ITERATIONS = 600_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)

    password_hash = hashlib.pbkdf2_hmac(
        HASH_NAME,
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )

    return (
        f"{HASH_NAME}$"
        f"{HASH_ITERATIONS}$"
        f"{salt.hex()}$"
        f"{password_hash.hex()}"
    )


def verify_password(
    password: str,
    stored_password_hash: str,
) -> bool:
    try:
        (
            hash_name,
            iterations_text,
            salt_hex,
            expected_hash_hex,
        ) = stored_password_hash.split("$")

        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(expected_hash_hex)
    except (TypeError, ValueError):
        return False

    if (
        hash_name != HASH_NAME
        or iterations != HASH_ITERATIONS
    ):
        return False

    calculated_hash = hashlib.pbkdf2_hmac(
        hash_name,
        password.encode("utf-8"),
        salt,
        iterations,
    )

    return hmac.compare_digest(
        calculated_hash,
        expected_hash,
    )