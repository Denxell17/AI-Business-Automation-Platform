import logging
from pathlib import Path



LOG_FILE = Path(__file__).with_name("activity.log")


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