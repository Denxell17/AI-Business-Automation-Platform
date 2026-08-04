
from activity_logger import log_activity
from payroll import (
    calculate_payroll,
    determine_performance,
)
from storage import (
    load_employees,
    save_employees,
)
from validators import (
    get_integer_in_range,
    get_positive_integer,
    get_required_text,
)



def display_header():
    print()
    print("=" * 40)
    print("EMPLOYEE MANAGEMENT SYSTEM".center(40))
    print("=" * 40)



def display_menu():
    print()
    print("1. Register Employee")
    print("2. View Employee Profile")
    print("3. View Payroll")
    print("4. Update Employee")
    print("5. Delete Employee")
    print("6. View All Employees")
    print("7. Exit")
    print()



def register_employee(employee_list):
    print()
    print("=" * 40)
    print("REGISTER EMPLOYEE".center(40))
    print("=" * 40)

    employee_id = get_required_text(
        "Enter Employee ID: ",
        "Employee ID"
    ).upper()

    existing_employee = find_employee_by_id(
        employee_list,
        employee_id
    )

    if existing_employee is not None:
        print("An Employee with that ID already exists.")
        return None

    employee = {
        "employee_id": employee_id, 

        "name": get_required_text(
            "Enter Employee Name: ",
            "Employee name"
        ),
        "department": get_required_text(
            "Enter Department: ",
            "Department"
        ),
        "position": get_required_text(
            "Enter Position: ",
            "Position"
        ),
        "country": get_required_text(   
            "Enter Country: ",
            "Country"
        ),
        "salary": get_positive_integer(
            "Enter Monthly Salary: ",
            "Salary"
        ),
        "email": get_required_text(
            "Enter Email: ",
            "Email"
        ),
        "phone_number": get_required_text(
            "Enter Phone Number: ",
            "Phone number"
        ),
        "years_of_experience": get_integer_in_range(
            "Enter Years of Experience: ",
            "Years of experience",
            0,
            60
        ),
        "company": get_required_text(
            "Enter Company: ",
            "Company"
        ),
        "employment_status": get_required_text(
            "Enter Employment Status: ",
            "Employment status"
        ),
        "performance_score": get_integer_in_range(
            "Enter Performance Score: ",
            "Performance score",
            0,
            100
        ),
    }

    return employee


def display_employee_profile(employee):
    print()
    print("=" * 40)
    print("EMPLOYEE PROFILE".center(40))
    print("=" * 40)

    print(f"Employee ID         : {employee['employee_id']}")
    print(f"Name                : {employee['name']}")
    print(f"Department          : {employee['department']}")
    print(f"Position            : {employee['position']}")
    print(f"Country             : {employee['country']}")
    print(f"Salary              : ₱{employee['salary']:,.2f}")
    print(f"Email               : {employee['email']}")
    print(f"Phone Number        : {employee['phone_number']}")
    print(f"Years of Experience : {employee['years_of_experience']}")
    print(f"Company             : {employee['company']}")
    print(f"Employment Status   : {employee['employment_status']}")
    print(f"Performance Score   : {employee['performance_score']}")


def display_payroll(employee):
    payroll = calculate_payroll(employee)

    print()
    print("=" * 40)
    print("PAYROLL SUMMARY".center(40))
    print("=" * 40)

    print(f"Employee            : {employee['name']}")
    print(f"Performance Rating  : {payroll['performance_rating']}")
    print(f"Bonus Rate          : {payroll['bonus_rate']:.0%}")
    print(f"Monthly Salary      : ₱{employee['salary']:,.2f}")
    print(f"Allowance           : ₱{payroll['allowance']:,.2f}")
    print(f"Overtime            : ₱{payroll['overtime']:,.2f}")
    print(f"Monthly Income      : ₱{payroll['monthly_income']:,.2f}")
    print(f"Annual Salary       : ₱{payroll['annual_salary']:,.2f}")
    print(f"13th-Month Pay      : ₱{payroll['thirteenth_month_pay']:,.2f}")
    print(f"Estimated Bonus     : ₱{payroll['estimated_bonus']:,.2f}")
    print(f"Monthly Tax (5%)    : ₱{payroll['monthly_tax']:,.2f}")
    print(f"Net Monthly Salary  : ₱{payroll['net_monthly_salary']:,.2f}")
    print(f"Net Monthly Income  : ₱{payroll['net_monthly_income']:,.2f}")
    print(f"Total Compensation  : ₱{payroll['total_compensation']:,.2f}")



def find_employee_by_id(employee_list, employee_id):
    employee_id = employee_id.strip().upper()

    for employee in employee_list:
        if employee["employee_id"].upper() == employee_id:
            return employee

    return None



def update_employee(employee_list):
    print()
    print("=" * 40)
    print("UPDATE EMPLOYEE".center(40))
    print("=" * 40)

    employee_id = input(
        "Enter Employee ID to update: "
    )

    employee = find_employee_by_id(
        employee_list,
        employee_id
    )

    if employee is None:
        print("Employee not found.")
        return False

    print()
    print(f"Current Department : {employee['department']}")
    print(f"Current Position   : {employee['position']}")

    new_department = input(
        "Enter new department "
        "(press Enter to keep current): "
    ).strip()

    new_position = input(
        "Enter new position "
        "(press Enter to keep current): "
    ).strip()

    if not new_department and not new_position:
        print("No changes entered. Employee was not updated.")
        return False

    if new_department:
        employee["department"] = new_department

    if new_position:
        employee["position"] = new_position

    print("Employee updated successfully.")
    return employee



def delete_employee(employee_list):
    print()
    print("=" * 40)
    print("DELETE EMPLOYEE".center(40))
    print("=" * 40)

    employee_id = input(
        "Enter Employee ID to delete: "
    )

    employee = find_employee_by_id(
        employee_list,
        employee_id
    )

    if employee is None:
        print("Employee not found.")
        return False

    print(f"Employee ID  : {employee['employee_id']}")
    print(f"Name         : {employee['name']}")

    confirmation = input(
        "Type YES to confirm deletion: "
    ).strip().upper()

    if confirmation != "YES":
        print("Deletion cancelled.")
        return False

    employee_list.remove(employee)
    print("Employee deleted successfully.")
    return employee



def display_all_employees(employee_list):
    print()
    print("=" * 60)
    print("EMPLOYEE DIRECTORY".center(60))
    print("=" * 60)
    print()

    if not employee_list:
        print("No employees registered yet.")
        return

    print(f"Total Employees: {len(employee_list)}")
    print()

    total_monthly_payroll = 0
    highest_paid_employee = employee_list[0]
    department_counts = {}

    for employee_number, employee in enumerate(
        employee_list,
        start=1
    ):

        total_monthly_payroll += employee["salary"]

        if employee["salary"] > highest_paid_employee["salary"]:
            highest_paid_employee = employee

        department = employee["department"]

        if department in department_counts:
            department_counts[department] += 1
        else:
            department_counts[department] = 1


        print("-" * 60)
        print(f"Employee #{employee_number}")
        print(f"Employee ID : {employee['employee_id']}")
        print(f"Name        : {employee['name']}")
        print(f"Department  : {employee['department']}")
        print(f"Position    : {employee['position']}")
        print(f"Salary      : ₱{employee['salary']:,.2f}")

    average_salary = (
        total_monthly_payroll / len(employee_list)
    )

    print("-" * 60)
    print("WORKFORCE SUMMARY".center(60))
    print("-" * 60)
    print(
        f"Total Monthly Payroll : "
        f"₱{total_monthly_payroll:,.2f}"
    )
    print(
        f"Average Salary        : "
        f"₱{average_salary:,.2f}"
    )
    print(
        f"Highest-Paid Employee : "
        f"{highest_paid_employee['name']}"
    )
    print(
        f"Highest Salary        : "
        f"₱{highest_paid_employee['salary']:,.2f}"
    )

    print()
    print("EMPLOYEES BY DEPARTMENT")
    print("-" * 60)

    for department, employee_count in department_counts.items():
        print(f"{department}: {employee_count}")

    print("-" * 60)


def run_program():
    display_header()
    log_activity("Application started.")

    employees = load_employees()

    if employees is None:
        print("Employee Management System could not start safely.")
        return
    
    employee = None

    while True:
        display_menu()
        choice = input("Choose an Option: ")

        if choice == "1":
            new_employee = register_employee(employees)

            if new_employee is not None:
                employees.append(new_employee)
                employee = new_employee

                records_saved = save_employees(employees)

                print()
                print(f"Welcome, {employee['name']}!")

                if records_saved:
                    print("Employee successfully registered and saved.")
                    log_activity(
                        f"Employee {employee['employee_id']} "
                        "registered and saved."
                    )
                else:
                    print(
                        "WARNING: Employee was added to the current session."
                        "but was not saved to the data file."
                    )
        elif choice == "2":
            employee_id = input(
                "Enter employee ID to view: "
            )

            employee = find_employee_by_id(
                employees,
                employee_id
            )

            if employee is None:
                print("Employee not found.")
            else:
                display_employee_profile(employee)
                log_activity(
                    f"Employee {employee['employee_id']} "
                    "profile viewed."
                )
        elif choice == "3":
            employee_id = input(
                "Enter Employee ID for payroll: "
            )

            employee = find_employee_by_id(
                employees,
                employee_id
            )

            if employee is None:
                print("Employee not found.")
            else:
                display_payroll(employee)
                log_activity(
                    f"Payroll viewed for employee "
                    f"{employee['employee_id']}."
                )
        elif choice == "4":
            employee_updated = update_employee(employees)

            if employee_updated:
                records_saved = save_employees(employees)

                if records_saved:
                    print("Employee changes saved.")
                    log_activity(
                        f"Employee {employee_updated['employee_id']} "
                        "updated and saved."
                    )
                else:
                    print(
                        "WARNING: Changes exist in the current session "
                        "but were not saved to the data file."
                    )

        elif choice == "5":
            employee_deleted = delete_employee(employees)

            if employee_deleted:
                records_saved = save_employees(employees)

                if records_saved:
                    print("Updated employee records saved.")
                    log_activity(
                        f"Employee {employee_deleted['employee_id']} "
                        "deleted and saved."
                    )
                else:
                    print(
                        "WARNING: The employee was removed from the "
                        "current session, but the deletion was not saved. "
                    )

        elif choice == "6":
            display_all_employees(employees)

        elif choice == "7":
            print("Closing the program...")
            log_activity("Application closed.")
            break   
        else:
            print("Invalid option. Please choose 1, 2, 3, 4, 5, 6, or 7.")

    print("Program closed successfully.")

if __name__ == "__main__":
    run_program()