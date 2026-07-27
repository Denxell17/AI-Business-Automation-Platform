# Day 5 Summary — Conditions and Business Decisions

## Goal

Teach the Employee Management System to make decisions using employee information.

## Topics Learned

- `if`
- `elif`
- `else`
- Comparison operators
- Assignment versus comparison
- Logical `and`
- Logical `or`
- Condition order
- Performance ratings
- Dynamic bonus rates
- Invalid-score detection
- Promotion eligibility
- Boundary values

## What Is a Condition?

A condition is an expression that produces either:

```python
True
```

or:

```python
False
```

Example:

```python
salary >= 50000
```

If:

```python
salary = 60000
```

then:

```python
salary >= 50000
```

is:

```python
True
```

Conditions allow a program to choose which instructions to run.

## Basic `if` Statement

```python
salary = 60000

if salary >= 50000:
    print("Employee qualifies for the higher salary level.")
```

Python runs the indented code only when the condition is true.

## `if` and `else`

```python
if salary >= 50000:
    print("Higher salary level")
else:
    print("Standard salary level")
```

The behavior is:

```text
Condition is true  → run the if block
Condition is false → run the else block
```

Only one of these blocks runs.

## Using `elif`

`elif` means “else if.” It checks another condition when earlier conditions are false:

```python
if performance_score >= 90:
    print("Outstanding")
elif performance_score >= 80:
    print("Very Good")
elif performance_score >= 70:
    print("Good")
else:
    print("Needs Improvement")
```

Python checks from top to bottom and stops at the first true condition.

For:

```python
performance_score = 88
```

Python checks:

```text
88 >= 90 → False
88 >= 80 → True
```

It prints:

```text
Very Good
```

It does not continue to the `>= 70` branch.

## Comparison Operators

```text
==   equal to
!=   not equal to
>    greater than
<    less than
>=   greater than or equal to
<=   less than or equal to
```

Examples:

```python
salary > 50000
salary < 100000
salary >= 60000
salary <= 60000
salary == 60000
salary != 50000
```

Each comparison produces `True` or `False`.

## Assignment Versus Comparison

A single equal sign assigns a value:

```python
salary = 60000
```

A double equal sign compares values:

```python
salary == 60000
```

Meaning:

```text
=   → store this value
==  → are these values equal?
```

Confusing these operators can cause incorrect behavior or a syntax error.

## Indentation

Code belonging to a condition must be indented:

```python
if salary >= 50000:
    print("Qualified")
```

Incorrect:

```python
if salary >= 50000:
print("Qualified")
```

Python uses indentation to understand which instructions belong to each block.

The standard indentation level is four spaces.

## Dynamic Performance Ratings

The program assigned a rating according to the score:

```python
if performance_score >= 90:
    performance_rating = "Outstanding"
elif performance_score >= 80:
    performance_rating = "Very Good"
elif performance_score >= 70:
    performance_rating = "Good"
else:
    performance_rating = "Needs Improvement"
```

Rating rules:

```text
90–100 → Outstanding
80–89  → Very Good
70–79  → Good
0–69   → Needs Improvement
```

## Dynamic Bonus Rates

The same conditions selected a bonus rate:

```python
if performance_score >= 90:
    performance_rating = "Outstanding"
    bonus_rate = 0.15
elif performance_score >= 80:
    performance_rating = "Very Good"
    bonus_rate = 0.10
elif performance_score >= 70:
    performance_rating = "Good"
    bonus_rate = 0.05
else:
    performance_rating = "Needs Improvement"
    bonus_rate = 0
```

Bonus rules:

```text
Outstanding       → 15%
Very Good         → 10%
Good              → 5%
Needs Improvement → 0%
```

The payroll calculation used the chosen rate:

```python
estimated_bonus = annual_salary * bonus_rate
```

This replaced the earlier fixed calculation:

```python
estimated_bonus = annual_salary * 0.10
```

## Formatting a Percentage

The bonus rate was displayed using:

```python
print(f"Bonus Rate: {bonus_rate:.0%}")
```

Examples:

```text
0.15 → 15%
0.10 → 10%
0.05 → 5%
0    → 0%
```

## Logical `or`

The program needed to detect scores outside the valid range:

```python
if performance_score < 0 or performance_score > 100:
    performance_rating = "Invalid Score"
    bonus_rate = 0
```

The `or` operator requires at least one condition to be true.

Examples:

```text
Score -10:
-10 < 0   → True
Result    → Invalid Score
```

```text
Score 150:
150 > 100 → True
Result    → Invalid Score
```

A normal score such as `88` makes both invalid conditions false.

## Logical `and`

The program used `and` for promotion eligibility:

```python
if 85 <= performance_score <= 100 and years_of_experience >= 2:
    promotion_status = "Eligible for Promotion Review"
else:
    promotion_status = "Not Yet Eligible for Promotion Review"
```

The `and` operator requires every connected condition to be true.

Examples:

```text
Score 90 and experience 3:
Both qualify → Eligible
```

```text
Score 90 and experience 1:
Experience does not qualify → Not eligible
```

```text
Score 80 and experience 3:
Score does not qualify → Not eligible
```

## Chained Comparisons

Python can check whether a value is between two limits:

```python
85 <= performance_score <= 100
```

This means:

```text
performance_score is at least 85
and
performance_score is no greater than 100
```

It helps reject a score such as `150`.

## Boundary Values

A boundary is where one category changes into another.

Important performance boundaries included:

```text
69 → Needs Improvement
70 → Good

79 → Good
80 → Very Good

89 → Very Good
90 → Outstanding

100 → Outstanding
101 → Invalid Score
```

Boundary testing confirms that comparison operators such as `>=` were chosen correctly.

## Important Correction: `>=`

An incorrect condition was written as:

```python
if performance_score >+ 90:
```

Python interprets this as:

```python
performance_score > (+90)
```

It means greater than positive 90, not greater than or equal to 90.

Correct:

```python
if performance_score >= 90:
```

This includes a score of exactly `90`.

## Important Correction: Variable Spelling

An `else` block used:

```python
performance_ratin = "Needs Improvement"
```

Later code tried to access:

```python
performance_rating
```

These are different variable names.

Correct:

```python
performance_rating = "Needs Improvement"
```

Python requires exact spelling. A missing letter can cause a `NameError`.

## Important Correction: Duplicate Bonus Calculation

The program initially calculated:

```python
estimated_bonus = annual_salary * 0.10
```

before determining the employee’s rating.

Later, it correctly calculated:

```python
estimated_bonus = annual_salary * bonus_rate
```

The fixed calculation was removed because:

- It duplicated the work.
- It always used 10%.
- It ignored the performance conditions.
- It could overwrite or conflict with the dynamic result.

## Complete Performance Logic

```python
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
    bonus_rate = 0.05
else:
    performance_rating = "Needs Improvement"
    bonus_rate = 0
```

The invalid-score condition appears first. Otherwise, a score such as `150` would satisfy:

```python
performance_score >= 90
```

and incorrectly receive an Outstanding rating.

## Testing Results

For a salary of:

```text
₱60,000 per month
```

A performance score of `90` produced:

```text
Rating            : Outstanding
Bonus Rate         : 15%
Estimated Bonus    : ₱108,000
Total Compensation : ₱888,000
```

A performance score of `60` produced:

```text
Rating            : Needs Improvement
Bonus Rate         : 0%
Estimated Bonus    : ₱0
Total Compensation : ₱780,000
```

These tests confirmed that the first and final branches worked.

## Day 5 Accomplishments

- Used `if`, `elif`, and `else`
- Compared numbers
- Distinguished assignment from comparison
- Created automatic performance ratings
- Created dynamic bonus rates
- Detected invalid scores
- Used `or`
- Used `and`
- Created promotion eligibility rules
- Tested boundary values
- Removed duplicate calculations
- Corrected comparison and spelling errors

## Important Things to Remember

```text
if      → check the first condition
elif    → check another condition
else    → fallback when earlier conditions are false

=       → assign a value
==      → compare values

and     → all connected conditions must be true
or      → at least one connected condition must be true
```

Condition order matters:

```text
Validate invalid input first
→ check highest category
→ check lower categories
→ use else as the fallback
```

## Personal Reflection

Day 5 taught the Employee Management System to make decisions based on business rules. Instead of applying the same bonus to every employee, the application began evaluating performance and selecting appropriate outcomes automatically.