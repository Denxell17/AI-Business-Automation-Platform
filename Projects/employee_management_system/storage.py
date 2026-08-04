import json
from pathlib import Path


DATA_FILE = Path(__file__).with_name("employees.json")


def load_employees(file_path=DATA_FILE):
    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        print()
        print("ERROR: The employee data file contains invalid JSON.")
        print("The application will stop to protect your data.")
        return None

    except OSError as error:
        print()
        print("ERROR: The employee data file could not be read.")
        print(f"Details: {error}")
        return None


def save_employees(employee_list, file_path=DATA_FILE):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(employee_list, file, indent=4)

        return True

    except OSError as error:
        print()
        print("ERROR: The employee records could not be saved.")
        print(f"Details: {error}")
        return False
