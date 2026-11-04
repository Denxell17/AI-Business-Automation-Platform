"""Run hourly with the application's database settings to enforce physical retention."""

from assistant_store import AssistantStore
from database import DATABASE_FILE


def main():
    AssistantStore(DATABASE_FILE).purge()
    print('Assistant retention maintenance completed.')


if __name__ == '__main__':
    main()
