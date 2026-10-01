import logging
import re
from datetime import datetime
from pathlib import Path

LOG_DIRECTORY = Path(__file__).with_name("logs")
LOG_FILE = LOG_DIRECTORY / "activity.log"
ACTIVITY_LOG_ENTRY_LIMIT = 100
ACTIVITY_LOG_ENTRY_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    r"(?:,\d{3})?) \| (?P<level>[A-Z]+) \| (?P<message>.*)$"
)


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


def build_activity_summaries(entries: list[str]) -> list[dict]:
    """Create safe Dashboard presentation data without changing log records."""
    summaries = []

    for entry in entries:
        match = ACTIVITY_LOG_ENTRY_PATTERN.fullmatch(entry)

        if match is None:
            summaries.append(
                {
                    "message": entry,
                    "level": None,
                    "recorded_at": None,
                }
            )
            continue

        stored_timestamp = match.group("timestamp")
        timestamp_format = (
            "%Y-%m-%d %H:%M:%S,%f"
            if "," in stored_timestamp
            else "%Y-%m-%d %H:%M:%S"
        )

        try:
            parsed_timestamp = datetime.strptime(
                stored_timestamp,
                timestamp_format,
            )
        except ValueError:
            summaries.append(
                {
                    "message": entry,
                    "level": None,
                    "recorded_at": None,
                }
            )
            continue

        summaries.append(
            {
                "message": match.group("message"),
                "level": match.group("level"),
                "recorded_at": parsed_timestamp.isoformat(
                    timespec=(
                        "milliseconds"
                        if "," in stored_timestamp
                        else "seconds"
                    )
                ),
            }
        )

    return summaries
