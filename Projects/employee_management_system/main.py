from getpass import getpass

from authorization import (
    BACKUP_DATABASE,
    DELETE_EMPLOYEE,
    EXPORT_REPORT,
    MANAGE_USER_ACCOUNTS,
    REGISTER_EMPLOYEE,
    RESTORE_DATABASE,
    UPDATE_EMPLOYEE,
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    user_has_permission,
)
from activity_logger import log_activity
from database_backup import run_database_backup
from database_restore import run_database_restoration
from payroll import calculate_payroll
from models import UserAccount, WorkforceSummary
from validators import (
    get_integer_in_range,
    get_positive_integer,
    get_required_text,
)
from employee_service import (
    filter_employees_by_department,
    filter_employees_by_salary_range,
    find_employee_by_id,
    remove_employee,
    search_employees_by_name,
    sort_employees_by_name,
    sort_employees_by_salary,
    update_employee_details,
)
from employee_repository import (
    load_employee_records,
    save_employee_records,
)
from user_service import authenticate_user_account
from user_account_setup import (
    run_current_user_password_change,
    run_viewer_account_password_reset,
    run_viewer_account_registration,
    run_viewer_account_status_change,
)
from reports import calculate_workforce_summary
from exporter import (
    EXPORT_FILE,
    export_employees_to_csv,
)

MENU_PERMISSIONS = {
    "1": REGISTER_EMPLOYEE,
    "2": VIEW_EMPLOYEE,
    "3": VIEW_PAYROLL,
    "4": UPDATE_EMPLOYEE,
    "5": DELETE_EMPLOYEE,
    "6": VIEW_EMPLOYEE,
    "7": VIEW_EMPLOYEE,
    "8": VIEW_EMPLOYEE,
    "9": VIEW_EMPLOYEE,
    "10": VIEW_EMPLOYEE,
    "11": EXPORT_REPORT,
    "12": BACKUP_DATABASE,
    "13": RESTORE_DATABASE,
    "14": MANAGE_USER_ACCOUNTS,
    "15": MANAGE_USER_ACCOUNTS,
    "16": MANAGE_USER_ACCOUNTS,
}


def login_user() -> UserAccount | None:
    print()
    print("USER LOGIN")

    username = input("Username: ").strip()
    password = getpass("Password: ")

    authenticated_user = authenticate_user_account(
        username,
        password,
    )

    if authenticated_user is None:
        print("Authentication failed.")
        log_activity("Failed login attempt.")
        return None

    print(
        f"Signed in as {authenticated_user['username']} "
        f"({authenticated_user['role']})."
    )
    log_activity(
        f"User {authenticated_user['username']} logged in."
    )
    return authenticated_user


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
    print("7. View Employees by Department")
    print("8. View Employees by Salary")
    print("9. Search Employees by Name")
    print("10. Filter Employees by Salary Range")
    print("11. Export Employee Report")
    print("12. Create SQLite Database Backup")
    print("13. Restore SQLite Database Backup")
    print("14. Register Viewer Account")
    print("15. Change Viewer Account Status")
    print("16. Reset Viewer Account Password")
    print("17. Change Your Password")
    print("18. Exit")


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

    changes_made = update_employee_details(
        employee,
        new_department,
        new_position,
    )

    if not changes_made:
        print("No changes entered. Employee was not updated.")
        return False

    print("Employee details updated successfully.")
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

    employee_removed = remove_employee(
        employee_list,
        employee
    )

    if not employee_removed:
        print("Employee could not be removed.")
        return False

    print("Employee deleted successfully.")
    return employee


def display_department_summary(
    summary: WorkforceSummary,
):
    department_counts = summary["department_counts"]
    department_payrolls = summary["department_payrolls"]
    department_average_salaries = summary[
        "department_average_salaries"
    ]

    print()
    print("EMPLOYEES BY DEPARTMENT")
    print("-" * 60)

    for department, employee_count in department_counts.items():
        print(f"{department}: {employee_count}")

    print("-" * 60)

    print()
    print("MONTHLY PAYROLL BY DEPARTMENT")
    print("-" * 60)

    for department, monthly_payroll in department_payrolls.items():
        print(f"{department}: ₱{monthly_payroll:,.2f}")

    print("-" * 60)

    print()
    print("AVERAGE SALARY BY DEPARTMENT")
    print("-" * 60)

    for department, average_salary in (
        department_average_salaries.items()
    ):
        print(f"{department}: ₱{average_salary:,.2f}")

    print("-" * 60)


def display_all_employees(employee_list):
    print()
    print("=" * 60)
    print("EMPLOYEE DIRECTORY".center(60))
    print("=" * 60)
    print()

    if not employee_list:
        print("No employees registered yet.")
        return

    summary = calculate_workforce_summary(employee_list)

    print(
        f"Total Employees: "
        f"{summary['total_employees']}"
    )
    print(
        f"Total Departments: "
        f"{summary['total_departments']}"
    )
    print()

    total_monthly_payroll = summary[
        "total_monthly_payroll"
    ]
    average_salary = summary["average_salary"]
    highest_paid_employee = summary[
        "highest_paid_employee"
    ]
    lowest_paid_employee = summary[
        "lowest_paid_employee"
    ]
    salary_range = summary["salary_range"]
    department_counts = summary["department_counts"]
    department_payrolls = summary["department_payrolls"]
    department_average_salaries = summary[
        "department_average_salaries"
    ]
    highest_payroll_department = summary[
        "highest_payroll_department"
    ]
    highest_average_salary_department = summary[
        "highest_average_salary_department"
    ]
    lowest_payroll_department = summary[
        "lowest_payroll_department"
    ]
    lowest_average_salary_department = summary[
        "lowest_average_salary_department"
    ]
    largest_department = summary["largest_department"]
    smallest_department = summary["smallest_department"]

    for employee_number, employee in enumerate(
        employee_list,
        start=1
    ):

        print("-" * 60)
        print(f"Employee #{employee_number}")
        print(f"Employee ID : {employee['employee_id']}")
        print(f"Name        : {employee['name']}")
        print(f"Department  : {employee['department']}")
        print(f"Position    : {employee['position']}")
        print(f"Salary      : ₱{employee['salary']:,.2f}")

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
    print(
        f"Lowest-Paid Employee  : "
        f"{lowest_paid_employee['name']}"
    )
    print(
        f"Lowest Salary         : "
        f"₱{lowest_paid_employee['salary']:,.2f}"
    )
    print(
        f"Salary Range          : "
        f"₱{salary_range:,.2f}"
    )
    print(
        f"Highest Payroll Dept. : "
        f"{highest_payroll_department}"
    )
    print(
        f"Department Payroll    : "
        f"₱{department_payrolls[highest_payroll_department]:,.2f}"
    )
    print(
        f"Highest Average Dept. : "
        f"{highest_average_salary_department}"
    )
    print(
        f"Department Average    : "
        f"₱{department_average_salaries[
            highest_average_salary_department
        ]:,.2f}"
    )
    print(
        f"Lowest Payroll Dept.  : "
        f"{lowest_payroll_department}"
    )
    print(
        f"Lowest Dept. Payroll  : "
        f"₱{department_payrolls[lowest_payroll_department]:,.2f}"
    )
    print(
        f"Lowest Average Dept.  : "
        f"{lowest_average_salary_department}"
    )
    print(
        f"Lowest Dept. Average  : "
        f"₱{department_average_salaries[lowest_average_salary_department]:,.2f}"
    )
    print(
        f"Largest Department    : "
        f"{largest_department}"
    )
    print(
        f"Department Employees  : "
        f"{department_counts[largest_department]}"
    )
    print(
        f"Smallest Department   : "
        f"{smallest_department}"
    )
    print(
        f"Department Employees  : "
        f"{department_counts[smallest_department]}"
    )

    display_department_summary(summary)


def register_viewer_user(
    current_user: UserAccount,
) -> bool:
    print()
    print("REGISTER VIEWER ACCOUNT")

    username = input("Viewer username: ").strip()
    password = getpass("Viewer password: ")
    password_confirmation = getpass(
        "Confirm viewer password: "
    )

    if not username or not password:
        print("Viewer username and password are required.")
        return False

    if password != password_confirmation:
        print("Viewer passwords do not match.")
        return False

    registration_succeeded = run_viewer_account_registration(
        current_user,
        username,
        password,
    )

    if registration_succeeded:
        log_activity(
            f"User {current_user['username']} registered "
            f"viewer account {username}."
        )

    return registration_succeeded


def change_viewer_account_status(
    current_user: UserAccount,
) -> bool:
    print()
    print("CHANGE VIEWER ACCOUNT STATUS")

    target_username = input(
        "Viewer username: "
    ).strip()

    if not target_username:
        print("Viewer username is required.")
        return False

    status_action = input(
        "Type ACTIVATE or DEACTIVATE: "
    ).strip().upper()

    if status_action == "ACTIVATE":
        is_active = True
    elif status_action == "DEACTIVATE":
        is_active = False
    else:
        print("Invalid viewer account status action.")
        return False

    status_changed = run_viewer_account_status_change(
        current_user,
        target_username,
        is_active,
    )

    if status_changed:
        status_text = (
            "activated"
            if is_active
            else "deactivated"
        )
        log_activity(
            f"User {current_user['username']} {status_text} "
            f"viewer account {target_username}."
        )

    return status_changed


def reset_viewer_password(
    current_user: UserAccount,
) -> bool:
    print()
    print("RESET VIEWER ACCOUNT PASSWORD")

    target_username = input(
        "Viewer username: "
    ).strip()

    new_password = getpass(
        "New viewer password: "
    )
    password_confirmation = getpass(
        "Confirm new viewer password: "
    )

    if (
        not target_username
        or not new_password.strip()
    ):
        print(
            "Viewer username and new password are required."
        )
        return False

    if new_password != password_confirmation:
        print("Viewer passwords do not match.")
        return False

    password_reset = run_viewer_account_password_reset(
        current_user,
        target_username,
        new_password,
    )

    if password_reset:
        log_activity(
            f"User {current_user['username']} reset password "
            f"for viewer account {target_username}."
        )

    return password_reset


def change_own_password(
    current_user: UserAccount,
) -> bool:
    print()
    print("CHANGE YOUR PASSWORD")

    current_password = getpass(
        "Current password: "
    )
    new_password = getpass(
        "New password: "
    )
    password_confirmation = getpass(
        "Confirm new password: "
    )

    if (
        not current_password.strip()
        or not new_password.strip()
    ):
        print("Current and new passwords are required.")
        return False

    if new_password != password_confirmation:
        print("New passwords do not match.")
        return False

    password_changed = run_current_user_password_change(
        current_user,
        current_password,
        new_password,
    )

    if password_changed:
        log_activity(
            f"User {current_user['username']} "
            "changed their password."
        )

    return password_changed


def run_program():
    display_header()
    log_activity("Application started.")

    authenticated_user = login_user()

    if authenticated_user is None:
        print("Employee Management System access denied.")
        log_activity("Application access denied.")
        return

    employees = load_employee_records()

    if employees is None:
        print("Employee Management System could not start safely.")
        return
    
    employee = None

    while True:
        display_menu()
        choice = input("Choose an Option: ")

        required_permission = MENU_PERMISSIONS.get(choice)

        if (
            required_permission is not None
            and not user_has_permission(
                authenticated_user,
                required_permission,
            )
        ):
            print("You do not have permission to use this option.")
            log_activity(
                f"User {authenticated_user['username']} was denied "
                f"permission {required_permission}."
            )
            continue

        if choice == "1":
            new_employee = register_employee(employees)

            if new_employee is not None:
                employees.append(new_employee)
                employee = new_employee

                records_saved = save_employee_records(
                    employees
                )

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
                        "WARNING: Employee was added to the current session. "
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
                records_saved = save_employee_records(
                    employees
                )

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
                records_saved = save_employee_records(
                    employees
                )

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
            sorted_employees = sort_employees_by_name(
                employees
            )
            display_all_employees(sorted_employees)

        elif choice == "7":
            department = input(
                "Enter department to filter: "
            )

            matching_employees = filter_employees_by_department(
                employees,
                department,
            )

            if not matching_employees:
                print("No employees found in that department.")
            else:
                sorted_matching_employees = sort_employees_by_name(
                    matching_employees
                )
                display_all_employees(sorted_matching_employees)
                log_activity(
                    "Employee directory filtered by department."
                )

        elif choice == "8":
            salary_ranked_employees = sort_employees_by_salary(
                employees
            )

            display_all_employees(salary_ranked_employees)
            log_activity(
                "Employee directory sorted by salary."
            )

        elif choice == "9":
            search_text = input(
                "Enter all or part of the employee name: "
            )

            matching_employees = search_employees_by_name(
                employees,
                search_text,
            )

            if not matching_employees:
                print("No employees found with that name.")
            else:
                sorted_matching_employees = sort_employees_by_name(
                    matching_employees
                )
                display_all_employees(sorted_matching_employees)
                log_activity(
                    "Employee directory searched by name."
                )

        elif choice == "10":
            minimum_salary = get_positive_integer(
                "Enter minimum salary: ",
                "Minimum salary",
            )
            maximum_salary = get_positive_integer(
                "Enter maximum salary: ",
                "Maximum salary",
            )

            if minimum_salary > maximum_salary:
                print(
                    "Minimum salary cannot be greater "
                    "than maximum salary."
                )
            else:
                matching_employees = filter_employees_by_salary_range(
                    employees,
                    minimum_salary,
                    maximum_salary,
                )

                if not matching_employees:
                    print("No employees found within that salary range.")
                else:
                    salary_ranked_employees = sort_employees_by_salary(
                        matching_employees
                    )
                    display_all_employees(salary_ranked_employees)
                    log_activity(
                        "Employee directory filtered by salary range."
                    )

        elif choice == "11":
            if not employees:
                print("No employees available to export.")
            else:
                export_successful = export_employees_to_csv(
                    employees
                )

                if export_successful:
                    print("Employee report exported successfully.")
                    print(f"Saved to: {EXPORT_FILE}")
                    log_activity(
                        "Employee CSV report exported."
                    )

        elif choice == "12":
            backup_successful = run_database_backup()

            if backup_successful:
                log_activity(
                    "SQLite database backup created."
                )

        elif choice == "13":
            print()
            print(
                "WARNING: This will replace the primary "
                "SQLite database."
            )
            confirmation = input(
                "Type RESTORE to continue: "
            ).strip().upper()

            if confirmation != "RESTORE":
                print("SQLite database restoration cancelled.")
            else:
                restoration_successful = (
                    run_database_restoration()
                )

                if restoration_successful:
                    restored_employees = (
                        load_employee_records("sqlite")
                    )

                    if restored_employees is None:
                        print(
                            "The restored SQLite employee "
                            "data could not be loaded."
                        )
                    else:
                        employees = restored_employees
                        employee = None

                        log_activity(
                            "SQLite database restored "
                            "from backup."
                        )

        elif choice == "14":
            register_viewer_user(authenticated_user)

        elif choice == "15":
            change_viewer_account_status(
                authenticated_user
            )

        elif choice == "16":
            reset_viewer_password(
                authenticated_user
            )

        elif choice == "17":
            change_own_password(
                authenticated_user
            )

        elif choice == "18":
            print("Closing the program...")
            log_activity("Application closed.")
            break
        else:
            print(
                "Invalid option. "
                "Please choose a number from 1 to 18."
            )

    print("Program closed successfully.")

if __name__ == "__main__":
    run_program()