import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from activity_logger import (
    ACTIVITY_LOG_ENTRY_LIMIT,
    build_activity_summaries,
    load_recent_activity_entries,
)


class TestActivityLogger(unittest.TestCase):
    def test_missing_log_returns_empty_list(self):
        with TemporaryDirectory() as temporary_directory:
            missing_log_file = (
                Path(temporary_directory) / "missing.log"
            )

            with patch(
                "activity_logger.LOG_FILE",
                missing_log_file,
            ):
                entries = load_recent_activity_entries()

        self.assertEqual(entries, [])

    def test_loads_latest_entries_newest_first(self):
        all_entries = [
            f"Activity entry {number}"
            for number in range(
                ACTIVITY_LOG_ENTRY_LIMIT + 2
            )
        ]

        with TemporaryDirectory() as temporary_directory:
            log_file = Path(temporary_directory) / "activity.log"
            log_file.write_text(
                "\n".join(all_entries) + "\n",
                encoding="utf-8",
            )

            with patch(
                "activity_logger.LOG_FILE",
                log_file,
            ):
                entries = load_recent_activity_entries()

        self.assertEqual(
            entries,
            list(reversed(all_entries[-ACTIVITY_LOG_ENTRY_LIMIT:])),
        )

    def test_unreadable_log_returns_none(self):
        with patch(
            "activity_logger.LOG_FILE"
        ) as mock_log_file:
            mock_log_file.open.side_effect = OSError(
                "The log file could not be read."
            )

            entries = load_recent_activity_entries()

        self.assertIsNone(entries)

    def test_dashboard_summaries_separate_known_metadata_without_changing_message(self):
        summaries = build_activity_summaries(
            [
                "2026-10-02 09:15:30,125 | INFO | "
                "User Example logged in | source retained.",
            ]
        )

        self.assertEqual(
            summaries,
            [
                {
                    "message": (
                        "User Example logged in | source retained."
                    ),
                    "level": "INFO",
                    "recorded_at": "2026-10-02T09:15:30.125",
                }
            ],
        )

    def test_dashboard_summaries_preserve_unrecognized_entries_verbatim(self):
        entry = "An older unstructured audit record | remains unchanged"

        self.assertEqual(
            build_activity_summaries([entry]),
            [
                {
                    "message": entry,
                    "level": None,
                    "recorded_at": None,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
