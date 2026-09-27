import csv
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from exporter import (
    build_employee_csv_content,
    export_employees_to_csv,
    neutralize_spreadsheet_text,
)


class TestEmployeeExporter(unittest.TestCase):

    def test_neutralizes_dangerous_spreadsheet_text_prefixes(self):
        cases = (
            ("=SUM(1,1)", "'=SUM(1,1)"),
            ("+cmd", "'+cmd"),
            ("-1+2", "'-1+2"),
            ("@SUM(A1:A2)", "'@SUM(A1:A2)"),
            ("  =SUM(1,1)", "'  =SUM(1,1)"),
            ("\t+cmd", "'\t+cmd"),
            ("\r\n@SUM(A1:A2)", "'\r\n@SUM(A1:A2)"),
            ("\x00-formula", "'\x00-formula"),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(
                    neutralize_spreadsheet_text(value),
                    expected,
                )

    def test_preserves_ordinary_exported_text(self):
        values = (
            "Dennis",
            "Automation = Operations",
            "123 Main Street",
            "",
            "東京",
            "'Already text",
        )

        for value in values:
            with self.subTest(value=value):
                self.assertEqual(neutralize_spreadsheet_text(value), value)

    def test_csv_protection_does_not_mutate_source_or_numeric_salary(self):
        employee = {
            "employee_id": "EMP001",
            "name": "=HYPERLINK(\"https://example.test\",\"Open\")",
            "department": "  +Finance",
            "position": "Developer",
            "salary": 60000,
        }
        original_employee = employee.copy()

        csv_content = build_employee_csv_content([employee])
        exported_row = next(csv.DictReader(StringIO(csv_content)))

        self.assertEqual(employee, original_employee)
        self.assertEqual(
            exported_row["name"],
            "'=HYPERLINK(\"https://example.test\",\"Open\")",
        )
        self.assertEqual(exported_row["department"], "'  +Finance")
        self.assertEqual(exported_row["position"], "Developer")
        self.assertEqual(exported_row["salary"], "60000")

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
