import csv
from pathlib import Path

from models import Employee


EXPORT_DIRECTORY = Path(__file__).with_name("exports")
EXPORT_FILE = EXPORT_DIRECTORY / "employee_report.csv"


def export_employees_to_csv(
    employee_list: list[Employee],
    file_path: Path = EXPORT_FILE,
) -> bool:
    fieldnames = [
        "employee_id",
        "name",
        "department",
        "position",
        "salary",
    ]

    try:
        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(employee_list)

        return True

    except OSError as error:
        print()
        print("ERROR: Employee report could not be exported.")
        print(f"Details: {error}")
        return False