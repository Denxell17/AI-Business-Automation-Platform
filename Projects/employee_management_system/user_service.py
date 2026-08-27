from pathlib import Path

from authorization import (
    MANAGE_USER_ACCOUNTS,
    user_has_permission,
)
from authentication import (
    hash_password,
    verify_password,
)
from database import (
    DATABASE_FILE,
    count_user_accounts,
    insert_user_account,
    load_user_account_by_username,
)
from models import UserAccount


def register_user_account(
    username: str,
    password: str,
    role: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    password_hash = hash_password(password)

    return insert_user_account(
        username,
        password_hash,
        role,
        database_file,
    )


def authenticate_user_account(
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> UserAccount | None:
    user_account = load_user_account_by_username(
        username,
        database_file,
    )

    if user_account is None:
        return None

    if not user_account["is_active"]:
        return None

    password_is_correct = verify_password(
        password,
        user_account["password_hash"],
    )

    if not password_is_correct:
        return None

    return user_account


def register_initial_administrator(
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    existing_account_count = count_user_accounts(
        database_file
    )

    if existing_account_count != 0:
        return False

    return register_user_account(
        username,
        password,
        "admin",
        database_file,
    )


def register_viewer_account(
    current_user: UserAccount,
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if (
        not current_user["is_active"]
        or not user_has_permission(
            current_user,
            MANAGE_USER_ACCOUNTS,
        )
    ):
        return False

    return register_user_account(
        username,
        password,
        "viewer",
        database_file,
    )