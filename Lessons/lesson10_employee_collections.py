employees = []

employee_one = {
    "employee_id": "EMP001",
    "name": "Dennis",
    "department": "Automation",
}

employee_two = {
    "employee_id": "EMP002",
    "name": "Maria",
    "department": "Finance",
}

employees.append(employee_one)
employees.append(employee_two)

def display_all_employees(employee_list):
    print()
    print(f"Total Employees: {len(employee_list)}")

    for employee_number, employee in enumerate(
        employee_list,
        start=1
    ):
        print("=" * 30)
        print(f"Employee #{employee_number}")
        print(f"Employee ID : {employee['employee_id']}")
        print(f"Name        : {employee['name']}")
        print(f"Department  : {employee['department']}")



def find_employee_by_id(employee_list, employee_id):
    for employee in employee_list:
        if employee["employee_id"] == employee_id:
            return employee

    return None

def add_employee(employee_list):
    print()
    print("ADD NEW EMPLOYEE".center(30))
    print("=" * 30)

    employee_id = input("Employee ID: ").strip().upper()

    if find_employee_by_id(employee_list, employee_id):
        print("An employee with that ID already exists.")
        return

    name = input("Name: ").strip()
    department = input("Department: ").strip()

    new_employee = {
        "employee_id": employee_id,
        "name": name,
        "department": department,
    }

    employee_list.append(new_employee)
    print(f"{name} was added successfully. ")
    


while True:
    print()
    print("=" * 35)
    print("EMPLOYEE COLLECTION MENU".center(35))
    print("=" * 35)
    print("1. Add Employee")
    print("2. View All Employees")
    print("3. Search Employee")
    print("4. EXIT")

    choice = input("Choose an option: ").strip()

    if choice == "1":
        add_employee(employees)

    elif choice == "2":
        display_all_employees(employees)

    elif choice == "3":
        print()

        search_id = input(
            "Input Employee ID to search: "
        ).strip().upper()

        employee_found = find_employee_by_id(
          employees,
          search_id  
        )

        if employee_found is None:
            print("Employee not found.")
        else:
            print()
            print("EMPLOYEE FOUND".center(30))
            print(
                f"Employee ID :"
                f"{employee_found['employee_id']}"
            )
            print(f"Name       : {employee_found['name']}")
            print(
                f"Department  : "
                f"{employee_found['department']}"
            )
    elif choice == "4":
        print("Closing employee collection. . .")
        break

    else:
        print("Invalid option. Please choose 1, 2, 3, or 4.")

print("Program closed successfully.")

    