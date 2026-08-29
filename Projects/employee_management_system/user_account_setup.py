from pathlib import Path

from database import DATABASE_FILE
from models import UserAccount
from user_service import (
    change_current_user_password,
    register_viewer_account,
    reset_viewer_account_password,
    set_viewer_account_active_status,
)


def run_viewer_account_registration(
    current_user: UserAccount,
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    registration_succeeded = register_viewer_account(
        current_user,
        username,
        password,
        database_file,
    )

    if not registration_succeeded:
        print("Viewer account was not created.")
        return False

    print("Viewer account created successfully.")
    return True


def run_viewer_account_status_change(
    current_user: UserAccount,
    target_username: str,
    is_active: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    status_changed = set_viewer_account_active_status(
        current_user,
        target_username,
        is_active,
        database_file,
    )

    if not status_changed:
        print("Viewer account status was not changed.")
        return False

    status_text = (
        "activated"
        if is_active
        else "deactivated"
    )

    print(
        f"Viewer account {status_text} successfully."
    )
    return True


def run_viewer_account_password_reset(
    current_user: UserAccount,
    target_username: str,
    new_password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    password_reset = reset_viewer_account_password(
        current_user,
        target_username,
        new_password,
        database_file,
    )

    if not password_reset:
        print("Viewer account password was not reset.")
        return False

    print("Viewer account password reset successfully.")
    return True


def run_current_user_password_change(
    current_user: UserAccount,
    current_password: str,
    new_password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    password_changed = change_current_user_password(
        current_user,
        current_password,
        new_password,
        database_file,
    )

    if not password_changed:
        print("Account password was not changed.")
        return False

    print("Account password changed successfully.")
    return True