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
    print("4. Exit")
    print()

def register_employee():
    print()
    print("=" * 40)
    print("REGISTER EMPLOYEE".center(40))
    print("=" * 40)

    employee = {
        "employee_id"         : input("Enter Employee ID: "),
        "name"                : input("Enter Employee Name: "),
        "department"          : input("Enter Department: "),
        "position"            : input("Position: "),
        "country"             : input("Enter Country: "),
        "salary"              : int(input("Enter Monthly Salary: ")),
        "email"               : input("Enter Email: "),
        "phone_number"        : input("Enter Phone Number: "),
        "years_of_experience" : int(input("Enter Years of Experience: ")),
        "company"             : input("Enter Company: "),
        "employment_status"   : input("Employment Status: "),
        "performance_score"   : int(input("Enter Performance Score (0-100): ")),
    }

    print()
    print(f"Welcome, {employee['name']}!")
    print("Employee successfully registered.")

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

def determine_performance(performance_score):
    if performance_score < 0 or performance_score > 100:
        return "Invalid Score", 0
    elif performance_score >= 90:
        return "Outstanding", 0.15
    elif performance_score >= 80:
        return "Very Good", 0.10
    elif performance_score >= 70:
        return "Good", 0.05
    else:
        return "Needs Improvement", 0

def calculate_payroll(employee):
    salary = employee["salary"]
    performance_rating, bonus_rate = determine_performance(
        employee["performance_score"]
    )

    annual_salary        = salary * 12
    thirteenth_month_pay = salary
    estimated_bonus      = annual_salary * bonus_rate
    monthly_tax          = salary * 0.05
    net_monthly_salary   = salary - monthly_tax
    allowance            = 5000
    overtime             = 3000
    monthly_income       = salary + allowance
    net_monthly_income   = salary + allowance + overtime - monthly_tax

    total_compensation = (
        annual_salary 
        + thirteenth_month_pay 
        + estimated_bonus
        )

    payroll = {
        "performance_rating"   : performance_rating,
        "bonus_rate"           : bonus_rate,
        "annual_salary"        : annual_salary,
        "thirteenth_month_pay" : thirteenth_month_pay,
        "estimated_bonus"      : estimated_bonus,
        "monthly_tax"          : monthly_tax,
        "net_monthly_salary"   : net_monthly_salary,
        "allowance"            : allowance,
        "overtime"             : overtime,
        "monthly_income"       : monthly_income,
        "net_monthly_income"   : net_monthly_income,
        "total_compensation"   : total_compensation,
    }
    return payroll

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

def run_program():
    display_header()
    employee = None

    while True:
        display_menu()
        choice = input("Choose an Option: ")

        if choice == "1":
            employee = register_employee()
        elif choice == "2":
            if employee is None:
                print("No Employee Registered Yet.")
            else:
                display_employee_profile(employee)
        elif choice == "3":
            if employee is None:
                print("No employee registered yet.")
            else:
                display_payroll(employee)        
        elif choice == "4":
            print("Closing the program...")
            break
        else:
            print("Invalid option. Please choose 1, 2, 3, or 4.")

    print("Program closed successfully.")

if __name__ == "__main__":
    run_program()