# Day 4 Summary — Python Operators and Payroll Calculations

## Goal

Learn how Python processes numeric data and use arithmetic operators to build a payroll calculator.

## Topics Learned

- Addition
- Subtraction
- Multiplication
- Division
- Floor division
- Modulo
- Exponentiation
- Percentage calculations
- Payroll calculations
- Currency formatting
- Calculation order

## Arithmetic Operators

Python provides operators for mathematical calculations:

```text
+    Addition
-    Subtraction
*    Multiplication
/    Division
//   Floor division
%    Modulo
**   Exponentiation
```

## Basic Operator Exercise

```python
a = 20
b = 5

print("Addition       :", a + b)
print("Subtraction    :", a - b)
print("Multiplication :", a * b)
print("Division       :", a / b)
print("Floor Division :", a // b)
print("Modulo         :", a % b)
print("Exponent       :", a ** b)
```

Output:

```text
Addition       : 25
Subtraction    : 15
Multiplication : 100
Division       : 4.0
Floor Division : 4
Modulo         : 0
Exponent       : 3200000
```

## Addition

Addition combines values:

```python
salary = 60000
allowance = 5000

monthly_income = salary + allowance
```

Result:

```text
65000
```

Business uses include:

- Adding salary and allowance
- Calculating invoice totals
- Combining expenses
- Adding product quantities

## Subtraction

Subtraction removes one value from another:

```python
salary = 60000
monthly_tax = 3000

net_monthly_salary = salary - monthly_tax
```

Result:

```text
57000
```

Business uses include:

- Deducting tax
- Calculating remaining budgets
- Subtracting discounts
- Reducing inventory

## Multiplication

Multiplication repeats or scales a value:

```python
monthly_salary = 60000
annual_salary = monthly_salary * 12
```

Result:

```text
720000
```

Business uses include:

- Monthly salary to annual salary
- Quantity multiplied by price
- Hours multiplied by hourly rate
- Calculating percentages

## Division

Regular division uses:

```python
/
```

Example:

```python
annual_salary = 720000
monthly_salary = annual_salary / 12
```

Result:

```text
60000.0
```

Regular division returns a floating-point number, even when the result is mathematically whole.

## Floor Division

Floor division uses:

```python
//
```

Example:

```python
17 // 5
```

Result:

```text
3
```

It divides and keeps the whole-number portion.

Floor division can be useful for:

- Creating complete groups
- Dividing items into full packages
- Calculating full work periods

## Modulo

Modulo uses:

```python
%
```

It returns the remainder after division:

```python
17 % 5
```

Result:

```text
2
```

Explanation:

```text
5 × 3 = 15
17 − 15 = 2
```

Modulo can later be used to:

- Check odd or even numbers
- Process every fifth employee
- Schedule repeating tasks
- Group records into batches

## Exponentiation

Exponentiation uses:

```python
**
```

Example:

```python
3 ** 2
```

means:

```text
3 × 3
```

Result:

```text
9
```

Another example:

```python
20 ** 5
```

means:

```text
20 × 20 × 20 × 20 × 20
```

Result:

```text
3200000
```

## Percentage Calculations

Percentages are represented as decimals:

```text
5%  = 0.05
10% = 0.10
15% = 0.15
```

Example:

```python
salary = 60000
monthly_tax = salary * 0.05
```

Result:

```text
3000
```

A 10% annual bonus:

```python
annual_salary = 720000
estimated_bonus = annual_salary * 0.10
```

Result:

```text
72000
```

## Payroll Calculations

The Employee Management System calculated:

```python
annual_salary = salary * 12
thirteenth_month_pay = salary
estimated_bonus = annual_salary * bonus_rate
monthly_tax = salary * 0.05
net_monthly_salary = salary - monthly_tax
```

Additional compensation values:

```python
allowance = 5000
overtime = 3000
```

Monthly income:

```python
monthly_income = salary + allowance
```

Net monthly income:

```python
net_monthly_income = (
    salary
    + allowance
    + overtime
    - monthly_tax
)
```

Total annual compensation:

```python
total_compensation = (
    annual_salary
    + thirteenth_month_pay
    + estimated_bonus
)
```

## Payroll Example

For:

```text
Monthly salary = ₱60,000
Allowance      = ₱5,000
Overtime       = ₱3,000
Tax rate       = 5%
Bonus rate     = 10%
```

The calculations are:

```text
Annual Salary       = 60,000 × 12
                    = ₱720,000

13th-Month Pay      = ₱60,000

Estimated Bonus     = 720,000 × 0.10
                    = ₱72,000

Monthly Tax         = 60,000 × 0.05
                    = ₱3,000

Net Monthly Salary  = 60,000 − 3,000
                    = ₱57,000

Monthly Income      = 60,000 + 5,000
                    = ₱65,000

Net Monthly Income  = 60,000 + 5,000 + 3,000 − 3,000
                    = ₱65,000

Total Compensation  = 720,000 + 60,000 + 72,000
                    = ₱852,000
```

## Important Correction: Allowance and Overtime

An earlier challenge incorrectly suggested subtracting allowance and overtime.

Incorrect:

```python
net_income = salary - allowance - overtime - tax
```

Allowance and overtime are normally additions to income.

Correct:

```python
net_income = salary + allowance + overtime - tax
```

The business meaning of each value determines whether it should be added or subtracted.

## Important Correction: 13th-Month Pay

The first total-compensation calculation included only annual salary and bonus:

```python
total_compensation = annual_salary + estimated_bonus
```

That produced:

```text
₱792,000
```

To include 13th-month pay:

```python
total_compensation = (
    annual_salary
    + thirteenth_month_pay
    + estimated_bonus
)
```

This produced:

```text
₱852,000
```

## Currency Formatting

Payroll values were formatted using f-strings:

```python
print(f"Monthly Salary: ₱{salary:,.2f}")
```

Formatting explanation:

```text
,     → thousands separator
.2f   → two decimal places
```

Example:

```text
60000 → ₱60,000.00
```

Payroll output:

```python
print(f"Monthly Salary      : ₱{salary:,.2f}")
print(f"Annual Salary       : ₱{annual_salary:,.2f}")
print(f"Estimated Bonus     : ₱{estimated_bonus:,.2f}")
print(f"Monthly Tax (5%)    : ₱{monthly_tax:,.2f}")
print(f"Net Monthly Salary  : ₱{net_monthly_salary:,.2f}")
print(f"Total Compensation  : ₱{total_compensation:,.2f}")
```

## Order of Operations

Python follows mathematical order:

1. Parentheses
2. Exponents
3. Multiplication and division
4. Addition and subtraction

Parentheses can make calculations clearer:

```python
net_monthly_income = (
    salary
    + allowance
    + overtime
    - monthly_tax
)
```

Even when parentheses are not required, they can improve readability.

## Business Meaning Matters

Python understands that `60000` is a number, but it does not automatically know that it represents salary.

The variable name supplies the meaning:

```python
salary = 60000
monthly_tax = 3000
allowance = 5000
```

Developers must understand the business rules before writing calculations.

A mathematically valid formula can still be wrong for the business if values are added or deducted incorrectly.

## Day 4 Accomplishments

- Practiced seven arithmetic operators
- Converted monthly salary into annual salary
- Calculated percentages
- Calculated tax and net salary
- Added allowance and overtime
- Calculated 13th-month pay
- Calculated performance bonus
- Calculated total compensation
- Formatted financial values professionally
- Corrected incorrect payroll formulas
- Turned employee data into useful business information

## Important Things to Remember

```text
+     → add
-     → subtract
*     → multiply
/     → divide and return a decimal
//    → divide and keep the whole-number portion
%     → return the remainder
**    → raise to a power
```

Percentage examples:

```python
five_percent = 0.05
ten_percent = 0.10
fifteen_percent = 0.15
```

Payroll pattern:

```text
Gross values
+ additional income
− deductions
= net income
```

## Personal Reflection

Day 4 changed the Employee Management System from an application that only collected information into an application that processed information. The payroll calculator demonstrated how basic Python operators can solve real business problems.