import logging
from pathlib import Path

LOG_DIRECTORY = Path(__file__).with_name("logs")
LOG_FILE = LOG_DIRECTORY / "activity.log"


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    encoding="utf-8",
)


def log_activity(message):
    logging.info(message)