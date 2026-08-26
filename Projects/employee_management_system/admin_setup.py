from getpass import getpass
from pathlib import Path

from database import DATABASE_FILE
from user_service import register_initial_administrator


def run_initial_administrator_setup(
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    setup_succeeded = register_initial_administrator(
        username,
        password,
        database_file,
    )

    if not setup_succeeded:
        print("Initial administrator account was not created.")
        return False

    print("Initial administrator account created successfully.")
    return True


def main() -> int:
    username = input(
        "Initial administrator username: "
    ).strip()
    password = getpass(
        "Initial administrator password: "
    )
    password_confirmation = getpass(
        "Confirm initial administrator password: "
    )

    if not username or not password:
        print("Administrator username and password are required.")
        return 1

    if password != password_confirmation:
        print("Administrator passwords do not match.")
        return 1

    setup_succeeded = run_initial_administrator_setup(
        username,
        password,
    )

    if not setup_succeeded:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())