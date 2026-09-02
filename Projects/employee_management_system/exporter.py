import csv
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
    writer.writerows(employee_list)

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
