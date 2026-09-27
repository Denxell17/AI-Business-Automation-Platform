import csv
import unicodedata
from io import StringIO
from pathlib import Path

from models import Employee


EXPORT_DIRECTORY = Path(__file__).with_name("exports")
EXPORT_FILE = EXPORT_DIRECTORY / "employee_report.csv"

CSV_FIELDNAMES = [
    "employee_id",
    "name",
    "department",
    "position",
    "salary",
]

CSV_TEXT_FIELDNAMES = (
    "employee_id",
    "name",
    "department",
    "position",
)

DANGEROUS_FORMULA_PREFIXES = frozenset("=+-@")


def neutralize_spreadsheet_text(value: str) -> str:
    """Keep exported text from being interpreted as a spreadsheet formula."""
    for character in value:
        if character.isspace() or unicodedata.category(character) == "Cc":
            continue
        if character in DANGEROUS_FORMULA_PREFIXES:
            return "'" + value
        break
    return value


def build_employee_csv_content(
    employee_list: list[Employee],
) -> str:
    output = StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_FIELDNAMES,
        extrasaction="ignore",
    )

    writer.writeheader()
    for employee in employee_list:
        export_row = employee.copy()
        for field_name in CSV_TEXT_FIELDNAMES:
            value = export_row.get(field_name)
            if isinstance(value, str):
                export_row[field_name] = neutralize_spreadsheet_text(
                    value
                )
        writer.writerow(export_row)

    return output.getvalue()


def export_employees_to_csv(
    employee_list: list[Employee],
    file_path: Path = EXPORT_FILE,
) -> bool:
    try:
        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            file.write(build_employee_csv_content(employee_list))

        return True

    except OSError as error:
        print()
        print("ERROR: Employee report could not be exported.")
        print(f"Details: {error}")
        return False
