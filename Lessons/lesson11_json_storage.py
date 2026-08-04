import json
from pathlib import Path

def load_employees(file_path):
    if not file_path.exists():
        print("No employee file found. Starting with an empty list.")
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


employees = [
    {
        "employee_id": "EMP001",
        "name": "Dennis",
        "department": "Automation",
    },
    {
        "employee_id": "EMP002",
        "name": "Maria",
        "department": "Finance",
    },
]

file_path = Path(__file__).with_name("employees.json")

def save_employees(file_path, employee_list):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(employee_list, file, indent=4)

    print("Employee records saved successfully.")
    print(f"Saved to: {file_path}")


loaded_employees = load_employees(file_path)

if not loaded_employees:
    loaded_employees = employees
    save_employees(file_path, loaded_employees)

new_employee = {
    "employee_id": "EMP003",
    "name": "Roxell",
    "department": "Human Resources"
}

employee_exists = False

for employee in loaded_employees:
    if employee["employee_id"] == new_employee["employee_id"]:
        employee_exists = True
        break

if employee_exists:
    print("EMP003 is already saved.")
else:
    loaded_employees.append(new_employee)
    save_employees(file_path, loaded_employees)
    print("EMP003 was added and saved.")

print("Employee records loaded successfully.")
print(f"Total employees loaded: {len(loaded_employees)}")

print()

for employee_number, employee in enumerate(
    loaded_employees,
    start=1
):
    print("=" * 30)
    print(f"Employee #{employee_number}")
    print(f"Employee ID : {employee['employee_id']}")
    print(f"Name        : {employee['name']}")
    print(f"Department  : {employee['department']}")
