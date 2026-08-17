# Day 24 Summary — Workforce Reporting Module

## Today’s Goal

Separate workforce calculations from terminal display code by creating a dedicated reporting module.

## New Files

```text
Projects/employee_management_system/reports.py
Projects/employee_management_system/test_reports.py
```

## Reporting Function

```python
def calculate_workforce_summary(employee_list):
    if not employee_list:
        return {
            "total_employees": 0,
            "total_monthly_payroll": 0,
            "average_salary": 0,
            "highest_paid_employee": None,
            "department_counts": {},
        }

    total_monthly_payroll = 0
    highest_paid_employee = employee_list[0]
    department_counts = {}

    for employee in employee_list:
        total_monthly_payroll += employee["salary"]

        if employee["salary"] > highest_paid_employee["salary"]:
            highest_paid_employee = employee

        department = employee["department"]

        if department in department_counts:
            department_counts[department] += 1
        else:
            department_counts[department] = 1

    average_salary = (
        total_monthly_payroll / len(employee_list)
    )

    return {
        "total_employees": len(employee_list),
        "total_monthly_payroll": total_monthly_payroll,
        "average_salary": average_salary,
        "highest_paid_employee": highest_paid_employee,
        "department_counts": department_counts,
    }
```

## Information Calculated

The report returns:

- Total number of employees
- Total monthly payroll
- Average employee salary
- Highest-paid employee
- Number of employees in each department

Example:

```python
{
    "total_employees": 2,
    "total_monthly_payroll": 110000,
    "average_salary": 55000,
    "highest_paid_employee": {
        "name": "Aki",
        "salary": 60000,
    },
    "department_counts": {
        "wertt": 1,
        "SSS": 1,
    },
}
```

## Empty Workforce Protection

The function checks:

```python
if not employee_list:
```

When no employees exist, it returns safe default values.

This prevents:

```python
0 / 0
```

which would cause a `ZeroDivisionError`.

For an empty workforce:

```python
{
    "total_employees": 0,
    "total_monthly_payroll": 0,
    "average_salary": 0,
    "highest_paid_employee": None,
    "department_counts": {},
}
```

## Highest-Paid Employee Logic

The first employee becomes the initial candidate:

```python
highest_paid_employee = employee_list[0]
```

This does not mean the first employee is always the highest-paid.

The loop checks every employee:

```python
if employee["salary"] > highest_paid_employee["salary"]:
    highest_paid_employee = employee
```

When a higher salary is found, that employee becomes the new candidate.

## Department Counting

The `department_counts` dictionary stores department names as keys and employee totals as values:

```python
{
    "Automation": 2,
    "Finance": 1,
}
```

The counting logic is:

```python
if department in department_counts:
    department_counts[department] += 1
else:
    department_counts[department] = 1
```

The first employee in a department creates the entry with a value of `1`. Additional employees increase that value.

## Separation of Responsibilities

Before Day 24, `display_all_employees()` both calculated and displayed workforce statistics.

After the refactor:

```text
reports.py
    Calculates workforce statistics.

main_refactored.py
    Displays employees and report results.

test_reports.py
    Verifies reporting calculations.
```

This avoids duplicated logic and makes the report easier to test, reuse, and maintain.

## Application Integration

`main_refactored.py` imports:

```python
from reports import calculate_workforce_summary
```

The display function requests the report:

```python
summary = calculate_workforce_summary(employee_list)
```

It then reads values such as:

```python
summary["total_employees"]
summary["total_monthly_payroll"]
summary["average_salary"]
summary["highest_paid_employee"]
summary["department_counts"]
```

## Automated Testing

The new reporting tests verify:

- Correct employee count
- Correct total monthly payroll
- Correct average salary
- Correct highest-paid employee
- Correct department counts
- Safe behavior for an empty employee list

Test result:

```text
Ran 2 tests
OK
```

Existing employee-system tests also remained successful:

```text
Ran 15 tests
OK
```

Total verified tests:

```text
17 tests passed
```

## Real Application Verification

The actual application displayed:

```text
Total Employees: 2
Total Monthly Payroll: ₱110,000.00
Average Salary: ₱55,000.00
Highest-Paid Employee: Aki
Highest Salary: ₱60,000.00
```

It also displayed correct employee totals for each department.

## Key Lesson

Calculation and presentation are different responsibilities.

A reporting module should calculate and return structured data. The main application should decide how to display that data.

This structure avoids duplication and prepares the reporting logic for future use in:

- Web dashboards
- REST APIs
- CSV exports
- Database reports
- AI-generated business summaries

## Day 24 Accomplishments

- Created `reports.py`.
- Created `test_reports.py`.
- Calculated total workforce size.
- Calculated total and average salary.
- Identified the highest-paid employee.
- Counted employees by department.
- Protected empty-list calculations.
- Integrated report results into the application.
- Passed all 17 automated tests.