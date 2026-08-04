# Day 14 Summary — Employee Directory and Workforce Reports

## Day 14 Goal

Day 14 added an employee directory and basic workforce reporting to the persistent Employee Management System.

The application can now:

- Display every saved employee
- Number employee records
- Count employees
- Calculate total monthly payroll
- Calculate average salary
- Identify the highest-paid employee
- Count employees by department

## Updated Menu

The application menu now includes:

```text
1. Register Employee
2. View Employee Profile
3. View Payroll
4. Update Employee
5. Delete Employee
6. View All Employees
7. Exit
```

Option `6` calls:

```python
display_all_employees(employees)
```

## Displaying All Employees

The directory function receives the complete employee list:

```python
def display_all_employees(employee_list):
```

It uses `enumerate()` to number every employee:

```python
for employee_number, employee in enumerate(
    employee_list,
    start=1
):
```

- `employee_number` contains 1, 2, 3, and so on.
- `employee` contains the current employee dictionary.
- `start=1` starts numbering at 1 instead of 0.

## Empty-List Protection

The function checks:

```python
if not employee_list:
    print("No employees registered yet.")
    return
```

This detects an empty list.

The early `return` prevents later code from running.

This is important because:

```python
employee_list[0]
```

would fail if no first employee existed.

This calculation would also fail:

```python
total_monthly_payroll / len(employee_list)
```

because dividing by zero is not allowed.

## Payroll Accumulator

The total begins at zero:

```python
total_monthly_payroll = 0
```

This variable is an accumulator. It collects salary values while the loop runs:

```python
total_monthly_payroll += employee["salary"]
```

Example:

```text
Starting total: 0
Add Aki:       0 + 60,000 = 60,000
Add Ruth: 60,000 + 50,000 = 110,000
```

Final total:

```text
₱110,000.00
```

## Average Salary

The average is calculated after the loop:

```python
average_salary = (
    total_monthly_payroll / len(employee_list)
)
```

The loop must finish first so the program has the complete payroll total.

Formula:

```text
Average salary = total monthly payroll ÷ employee count
```

Current calculation:

```text
₱110,000 ÷ 2 = ₱55,000
```

## Finding the Highest-Paid Employee

The program starts by treating the first employee as the current highest-paid employee:

```python
highest_paid_employee = employee_list[0]
```

`[0]` means the first item in a Python list.

Inside the loop, each salary is compared with the remembered highest salary:

```python
if employee["salary"] > highest_paid_employee["salary"]:
    highest_paid_employee = employee
```

If the current employee earns more, the program remembers that employee instead.

Current result:

```text
Highest-Paid Employee : Aki
Highest Salary        : ₱60,000.00
```

## Counting Employees by Department

The department counter begins as an empty dictionary:

```python
department_counts = {}
```

For every employee, the program gets the department:

```python
department = employee["department"]
```

If the department already exists in the dictionary, its count increases:

```python
if department in department_counts:
    department_counts[department] += 1
```

If it is a new department, its count starts at one:

```python
else:
    department_counts[department] = 1
```

Example result:

```python
{
    "Automation": 2,
    "Finance": 3,
}
```

This means two employees belong to Automation and three belong to Finance.

## Displaying Department Counts

The program uses `.items()`:

```python
for department, employee_count in department_counts.items():
    print(f"{department}: {employee_count}")
```

`.items()` provides:

```text
department     → dictionary key
employee_count → dictionary value
```

## Current Workforce Report

The completed report displays:

```text
Total Monthly Payroll : ₱110,000.00
Average Salary        : ₱55,000.00
Highest-Paid Employee : Aki
Highest Salary        : ₱60,000.00

EMPLOYEES BY DEPARTMENT
wertt: 1
SSS: 1
```

## Day 14 Accomplishments

- Added an employee directory menu option
- Displayed all persistent employee records
- Used `enumerate()` for numbering
- Protected calculations from an empty list
- Used an accumulator
- Calculated total monthly payroll
- Calculated average salary
- Found the highest-paid employee
- Counted employees by department
- Produced a useful workforce summary

## Important Things to Remember

```text
employee_list[0]      → first employee dictionary
len(employee_list)    → number of employees
accumulator           → variable that collects a total
+=                    → add to the current value
average               → total divided by count
department_counts     → dictionary containing department totals
.items()              → dictionary keys and values
```

## Cost Note

The directory and workforce reports run locally and remain completely free. They do not require paid APIs, cloud services, or a credit card.

## Personal Reflection

Day 14 expanded the project beyond storing employee records. The application now analyzes workforce data and produces business information that HR staff could use.