from pathlib import Path

from authorization import (
    MANAGE_USER_ACCOUNTS,
    user_has_permission,
)
from authentication import (
    DUMMY_PASSWORD,
    DUMMY_PASSWORD_HASH,
    hash_password,
    verify_password,
)
from database import (
    DATABASE_FILE,
    count_user_accounts,
    insert_user_account,
    load_user_account_by_username,
    update_user_account_active_status,
    update_user_account_password_hash,
)
from models import UserAccount
from password_policy import (
    password_is_safe_to_verify,
    password_meets_policy,
)


def register_user_account(
    username: str,
    password: str,
    role: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if not password_meets_policy(username, password):
        return False
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

    active_user = (
        user_account
        if user_account is not None and user_account["is_active"]
        else None
    )
    password_is_bounded = password_is_safe_to_verify(password)
    password_is_correct = verify_password(
        password if password_is_bounded else DUMMY_PASSWORD,
        (
            active_user["password_hash"]
            if active_user is not None and password_is_bounded
            else DUMMY_PASSWORD_HASH
        ),
    )

    if active_user is None or not password_is_bounded or not password_is_correct:
        return None

    return active_user


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

    if (
        not username.strip()
        or not password.strip()
    ):
        return False

    return register_user_account(
        username,
        password,
        "viewer",
        database_file,
    )


def set_viewer_account_active_status(
    current_user: UserAccount,
    target_username: str,
    is_active: bool,
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

    target_user = load_user_account_by_username(
        target_username,
        database_file,
    )

    if target_user is None:
        return False

    if target_user["role"] != "viewer":
        return False

    if target_user["is_active"] == is_active:
        return False

    return update_user_account_active_status(
        target_username,
        is_active,
        database_file,
    )


def reset_viewer_account_password(
    current_user: UserAccount,
    target_username: str,
    new_password: str,
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

    if not password_meets_policy(target_username, new_password):
        return False

    target_user = load_user_account_by_username(
        target_username,
        database_file,
    )

    if target_user is None:
        return False

    if target_user["role"] != "viewer":
        return False

    if verify_password(
        new_password,
        target_user["password_hash"],
    ):
        return False

    new_password_hash = hash_password(new_password)

    return update_user_account_password_hash(
        target_username,
        new_password_hash,
        database_file,
    )


def change_current_user_password(
    current_user: UserAccount,
    current_password: str,
    new_password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if not current_user["is_active"]:
        return False

    if not current_password.strip():
        return False

    stored_user = load_user_account_by_username(
        current_user["username"],
        database_file,
    )

    if stored_user is None:
        return False

    if not stored_user["is_active"]:
        return False

    if stored_user["user_id"] != current_user["user_id"]:
        return False

    if not password_meets_policy(stored_user["username"], new_password):
        return False

    if not verify_password(
        current_password,
        stored_user["password_hash"],
    ):
        return False

    if verify_password(
        new_password,
        stored_user["password_hash"],
    ):
        return False

    new_password_hash = hash_password(new_password)

    return update_user_account_password_hash(
        stored_user["username"],
        new_password_hash,
        database_file,
    )
