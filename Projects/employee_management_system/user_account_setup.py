from pathlib import Path

from database import DATABASE_FILE
from models import UserAccount
from user_service import register_viewer_account


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