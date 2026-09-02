import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from exporter import (
    build_employee_csv_content,
    export_employees_to_csv,
)


class TestEmployeeExporter(unittest.TestCase):

    def test_build_employee_csv_content_uses_report_columns(self):
        csv_content = build_employee_csv_content(
            [
                {
                    "employee_id": "EMP001",
                    "name": "Dennis",
                    "department": "Automation",
                    "position": "Developer",
                    "salary": 60000,
                    "email": "private@example.com",
                }
            ]
        )

        csv_rows = list(csv.DictReader(csv_content.splitlines()))

        self.assertEqual(
            csv_rows[0],
            {
                "employee_id": "EMP001",
                "name": "Dennis",
                "department": "Automation",
                "position": "Developer",
                "salary": "60000",
            },
        )

    def test_export_employees_to_csv(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
                "department": "Automation",
                "position": "Developer",
                "salary": 60000,
                "email": "private@example.com",
            }
        ]

        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employee_report.csv"
            )

            export_result = export_employees_to_csv(
                employees,
                test_file,
            )

            with open(
                test_file,
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                exported_rows = list(
                    csv.DictReader(file)
                )

        self.assertTrue(export_result)
        self.assertEqual(len(exported_rows), 1)
        self.assertEqual(
            exported_rows[0]["employee_id"],
            "EMP001",
        )
        self.assertEqual(
            exported_rows[0]["name"],
            "Dennis",
        )
        self.assertNotIn(
            "email",
            exported_rows[0],
        )


    def test_export_empty_employee_list(self):
        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "empty_report.csv"
            )

            export_result = export_employees_to_csv(
                [],
                test_file,
            )

            with open(
                test_file,
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                reader = csv.DictReader(file)
                exported_rows = list(reader)
                exported_columns = reader.fieldnames

            self.assertTrue(export_result)
            self.assertEqual(exported_rows, [])
            self.assertEqual(
                exported_columns,
                [
                    "employee_id",
                    "name",
                    "department",
                    "position",
                    "salary",
                ],
            )


if __name__ == "__main__":
    unittest.main()
