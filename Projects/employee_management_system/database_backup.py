from database import backup_database


def run_database_backup() -> bool:
    backup_succeeded = backup_database()

    if not backup_succeeded:
        print("SQLite database backup was not created.")
        return False

    print("SQLite database backup completed successfully.")
    return True


if __name__ == "__main__":
    backup_succeeded = run_database_backup()

    if not backup_succeeded:
        raise SystemExit(1)