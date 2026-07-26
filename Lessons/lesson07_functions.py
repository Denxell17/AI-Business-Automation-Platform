# All function definitions

def display_welcome_message():
    print("=" * 40)
    print("EMPLOYEE MANAGEMENT SYSTEM".center(40))
    print("=" * 40)

def greet_employee(name):
    print(f"Welcome, {name}!")
    print("Employee successfully registered.")

def calculate_annual_salary(monthly_salary):
    annual_salary = monthly_salary * 12
    return annual_salary

def calculate_bonus(annual_salary, bonus_rate):
    bonus = annual_salary * bonus_rate
    return bonus

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


# Main program: all function calls

display_welcome_message()
greet_employee("Dennis")

yearly_salary = calculate_annual_salary(60000)
performance_rating, bonus_rate = determine_performance(88)
estimated_bonus = calculate_bonus(yearly_salary, bonus_rate)

print(f"Annual Salary: ₱{yearly_salary:,.2f}")
print(f"Estimated Bonus: ₱{estimated_bonus:,.2f}")
print(f"Performance Rating: {performance_rating}")
print(f"Bonus Rate: {bonus_rate:.0%}")