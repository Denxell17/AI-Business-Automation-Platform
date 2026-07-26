print()
print("="*40)
print("EMPLOYEE MANAGEMENT SYSTEM".center(40))
print("="*40)

#Collect Employee Information

employee_id = input("Enter Employee ID: ")
name = input("Enter Employee Name: ")
department = input("Enter Department: ")
position = input("Enter Position: ")
country = input("Enter Country: ")
salary = int(input("Enter Salary: "))
email = input("Enter Email: ")
phone_number = input("Enter Phone Number: ")
years_of_experience = int(input("Enter Year of Experience: "))
company = input("Enter Company: ")
employment_status = input("Enter Employment Status: ")
performance_score = int(input("Enter Performance Score (0-100): "))

#Determine performance rating and bonus rate

if performance_score < 0 or performance_score > 100:
    performance_rating = "Invalid Score"
    bonus_rate = 0
elif performance_score >= 90:
    performance_rating = "Outstanding"
    bonus_rate = 0.15
elif performance_score >= 80:
    performance_rating = "Very Good"
    bonus_rate = 0.10
elif performance_score >= 70:
    performance_rating = "Good"
    bonus_rate = .05
else:
    performance_rating = "Needs Improvement"
    bonus_rate = 0

if 85 <= performance_score <= 100 and years_of_experience >= 2:
    promotion_status = "Eligible for Promotion Review"
else:
    promotion_status = "Not Eligible for Promotion Review"


print()

print(f"Welcome, {name}!")
print("Employee Successfully Registered.")

print()

#Employee Profile
print("Employee Profile".center(40))
print("-"*40)
print(f"Employee ID          : {employee_id}")
print(f"Name                 : {name}")
print(f"Department           : {department}")
print(f"Position             : {position}")
print(f"Country              : {country}")
print(f"Salary               : ₱{salary:,.2f}")
print(f"Email                : {email}")
print(f"Phone Number         : {phone_number}")
print(f"Years of Experience  : {years_of_experience}")
print(f"Company              : {company}")
print(f"Employment Status    : {employment_status}")
print(f"Performance Score    : {performance_score}")
print(f"Performance Rating   : {performance_rating}")
print(f"Bonus Rate           : {bonus_rate:.0%}")
print(f"Promotion Status     : {promotion_status}")



print()

print("=" * 40)
print("PAYROLL SUMMARY".center(40))
print("=" * 40)

# Perform payroll calculations

annual_salary = salary * 12
thirteenth_month_pay = salary
estimated_bonus = annual_salary * bonus_rate
monthly_tax = salary * 0.05
net_monthly_salary = salary - monthly_tax
allowance = 5000
overtime = 3000
monthly_income = salary + allowance
net_monthly_income = salary + allowance + overtime - monthly_tax
total_compensation = (annual_salary + thirteenth_month_pay + estimated_bonus)

#Payroll Summary

print(f"Monthly Salary      : ₱{salary:,.2f}")
print(f"Allowance           : ₱{allowance:,.2f}")
print(f"Overtime            : ₱{overtime:,.2f}")
print(f"Monthly Income      : ₱{monthly_income:,.2f}")
print(f"Annual Salary       : ₱{annual_salary:,.2f}")
print(f"13th-Month Pay      : ₱{thirteenth_month_pay:,.2f}")
print(f"Estimated Bonus     : ₱{estimated_bonus:,.2f}")
print(f"Monthly Tax (5%)    : ₱{monthly_tax:,.2f}")
print(f"Net Monthly Salary  : ₱{net_monthly_salary:,.2f}")
print(f"Net Monthly Income  : ₱{net_monthly_income:,.2f}")
print(f"Total Compensation  : ₱{total_compensation:,.2f}")

