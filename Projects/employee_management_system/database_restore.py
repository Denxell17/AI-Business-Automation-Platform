from database import restore_database_from_backup


def run_database_restoration() -> bool:
    restoration_succeeded = (
        restore_database_from_backup()
    )

    if not restoration_succeeded:
        print("SQLite database restoration was not completed.")
        return False

    print("SQLite database restored successfully.")
    return True


if __name__ == "__main__":
    confirmation = input(
        "TYPE RESTORE to replace the primary SQLite database: "
    ).strip().upper()

    if confirmation != "RESTORE":
        print("SQLite database restoration cancelled.")
    else:
        restoration_succeeded = run_database_restoration()

        if not restoration_succeeded:
            raise SystemExit(1)