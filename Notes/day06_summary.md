# Day 6 Summary — Loops and Repeating Menus

## Goal

Learn how to repeat instructions and build a menu that continues running until the user chooses to exit.

## Topics Learned

- `while` loops
- `for` loops
- Counters
- `range()`
- `break`
- `continue`
- Infinite loops
- Loop indentation
- Repeating application menus
- Invalid menu-option handling

## What Is a Loop?

A loop repeats a block of code.

Without a loop:

```python
print("Employee 1")
print("Employee 2")
print("Employee 3")
```

With a loop:

```python
for employee_number in range(1, 4):
    print(f"Employee {employee_number}")
```

Loops reduce repetitive code and allow programs to process changing amounts of data.

## The `while` Loop

A `while` loop repeats while its condition remains true:

```python
count = 1

while count <= 5:
    print(f"Count: {count}")
    count = count + 1

print("Loop finished.")
```

Output:

```text
Count: 1
Count: 2
Count: 3
Count: 4
Count: 5
Loop finished.
```

## How the Counter Loop Works

The counter begins at:

```python
count = 1
```

Python checks:

```python
count <= 5
```

The sequence is:

```text
count = 1 → condition true → print 1 → increase to 2
count = 2 → condition true → print 2 → increase to 3
count = 3 → condition true → print 3 → increase to 4
count = 4 → condition true → print 4 → increase to 5
count = 5 → condition true → print 5 → increase to 6
count = 6 → condition false → leave the loop
```

Python then continues with the first non-indented line:

```python
print("Loop finished.")
```

## Updating a Counter

This:

```python
count = count + 1
```

can be shortened to:

```python
count += 1
```

Both increase `count` by one.

Other update operators include:

```python
count -= 1
total += amount
salary *= 2
```

## Infinite Loops

If the counter is never updated:

```python
count = 1

while count <= 5:
    print(count)
```

`count` remains `1`, so the condition remains true forever.

This creates an infinite loop.

An accidental running loop can usually be stopped with:

```text
Ctrl + C
```

## Code Inside and Outside a Loop

Indentation determines whether code belongs to a loop:

```python
while count <= 5:
    print(count)             # Inside
    count += 1               # Inside

print("Loop finished.")      # Outside
```

The code inside repeats. The code outside runs after the loop ends.

## The `for` Loop

A `for` loop processes values from a sequence:

```python
for employee_number in range(1, 6):
    print(f"Processing Employee #{employee_number}")
```

Output:

```text
Processing Employee #1
Processing Employee #2
Processing Employee #3
Processing Employee #4
Processing Employee #5
```

The variable `employee_number` receives a new value during every repetition.

## Understanding `range()`

```python
range(1, 6)
```

generates:

```text
1, 2, 3, 4, 5
```

The starting value is included, but the ending value is excluded.

General form:

```python
range(start, stop)
```

Example:

```python
range(3, 8)
```

produces:

```text
3, 4, 5, 6, 7
```

## `while` Versus `for`

Use `while` when repetition depends on a condition:

```python
while choice != "4":
```

Use `for` when processing a known sequence or range:

```python
for employee_number in range(1, 6):
```

Simple comparison:

```text
while → repeat while something remains true
for   → repeat for every value in a sequence
```

## The `continue` Statement

`continue` skips the rest of the current repetition and moves to the next one:

```python
for employee_number in range(1, 6):
    if employee_number == 3:
        print("Employee #3 skipped.")
        continue

    print(f"Processing Employee #{employee_number}")

print("Processing completed.")
```

Output:

```text
Processing Employee #1
Processing Employee #2
Employee #3 skipped.
Processing Employee #4
Processing Employee #5
Processing completed.
```

When the number is `3`, Python reaches `continue`, so this line is skipped for that repetition:

```python
print(f"Processing Employee #{employee_number}")
```

The loop itself continues.

## The `break` Statement

`break` exits the entire loop:

```python
while True:
    choice = input("Choose an option: ")

    if choice == "3":
        print("Closing the program...")
        break
```

Once `break` runs, Python leaves the `while` loop.

## `break` Versus `continue`

```text
continue → skip the current repetition
break    → stop the entire loop
```

Example:

```python
for number in range(1, 6):
    if number == 2:
        continue

    if number == 4:
        break

    print(number)
```

Output:

```text
1
3
```

Explanation:

- `2` is skipped by `continue`.
- `4` ends the loop with `break`.
- `5` is never processed.

## Intentional Infinite Loop

This loop is intentionally endless:

```python
while True:
```

It is useful for a menu that should keep running.

The loop must provide a safe exit:

```python
if choice == "3":
    break
```

Without `break`, the user could not close the program normally.

## Repeating Employee Menu

You built:

```python
while True:
    print("=" * 40)
    print("EMPLOYEE MANAGEMENT MENU".center(40))
    print("=" * 40)
    print("1. Register Employee")
    print("2. View Payroll")
    print("3. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        print("Register Employee selected.")
    elif choice == "2":
        print("View Payroll selected.")
    elif choice == "3":
        print("Closing the program...")
        break
    else:
        print("Invalid option. Please choose 1, 2, or 3.")

    print()

print("Program closed successfully.")
```

## Menu Flow

```text
Display menu
→ Ask for choice
→ Process the choice
→ Return to menu
→ Repeat
→ Exit when the user selects 3
```

The program no longer needed to restart after every action.

## Handling Invalid Options

The `else` branch handled unexpected choices:

```python
else:
    print("Invalid option. Please choose 1, 2, or 3.")
```

If the user entered:

```text
5
```

the application displayed the error and returned to the menu.

This is better than crashing or silently doing nothing.

## Why Menu Choices Were Strings

The choice came from:

```python
choice = input("Choose an option: ")
```

Because `input()` returns a string, comparisons used quotation marks:

```python
if choice == "1":
```

not:

```python
if choice == 1:
```

The first compares a string with a string.

## Important Correction: Missing `break`

The first menu version printed:

```python
print("Closing the program...")
```

but did not contain:

```python
break
```

The loop therefore continued displaying the menu.

The correction was:

```python
elif choice == "3":
    print("Closing the program...")
    break
```

## Important Correction: Completion Message Indentation

This line was initially placed inside the `for` loop:

```python
print("Processing completed.")
```

It printed repeatedly.

It was moved outside:

```python
for employee_number in range(1, 6):
    print(employee_number)

print("Processing completed.")
```

Now it runs once after all employees are processed.

## Standard Indentation

Python generally uses four spaces per indentation level:

```python
while True:
    if choice == "1":
        print("Selected")
```

Indentation levels:

```text
while block       → 4 spaces
if inside while   → 8 spaces
```

Consistent indentation improves readability and prevents errors.

## Business Uses of Loops

Loops will eventually allow the platform to:

- Process multiple employees
- Read multiple documents
- Analyze spreadsheet rows
- Send multiple notifications
- Repeat a menu
- Search collections of records
- Process automation tasks
- Continue working until the user exits

## Day 6 Accomplishments

- Created a counter loop
- Used `while`
- Used `for`
- Generated numbers with `range()`
- Prevented an accidental infinite loop
- Used `continue` to skip one item
- Used `break` to end a loop
- Built a repeating menu
- Handled invalid menu choices
- Practiced nested indentation
- Prepared the application for reusable functions

## Important Things to Remember

```text
while condition:  → repeat while the condition is true
for item in data: → repeat for every item
range(1, 6)       → generates 1 through 5
count += 1        → increases a counter
continue          → skip this repetition
break             → exit the loop
Ctrl + C          → stop an accidental running loop
```

Menu pattern:

```python
while True:
    choice = input("Choose: ")

    if choice == "exit":
        break
```

## Personal Reflection

Day 6 gave the Employee Management System a repeating workflow. The menu became the control center that would later call registration, profile, and payroll functions without restarting the application.