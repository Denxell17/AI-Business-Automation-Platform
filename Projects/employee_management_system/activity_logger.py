import logging
from pathlib import Path

LOG_DIRECTORY = Path(__file__).with_name("logs")
LOG_FILE = LOG_DIRECTORY / "activity.log"
ACTIVITY_LOG_ENTRY_LIMIT = 100


LOG_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

activity_logger = logging.getLogger("abap.activity")
activity_logger.setLevel(logging.INFO)
activity_logger.propagate = False

if not activity_logger.handlers:
    activity_log_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )
    activity_log_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        )
    )
    activity_logger.addHandler(activity_log_handler)


def log_activity(message):
    activity_logger.info(message)


def load_recent_activity_entries() -> list[str] | None:
    try:
        with LOG_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            entries = file.readlines()
    except FileNotFoundError:
        return []
    except (OSError, UnicodeError):
        return None

    recent_entries = entries[-ACTIVITY_LOG_ENTRY_LIMIT:]

    return [
        entry.rstrip("\r\n")
        for entry in reversed(recent_entries)
    ]