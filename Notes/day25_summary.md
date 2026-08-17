# Day 25 Summary — Export Employee Reports to CSV

## Today’s Goal

Add a local CSV export feature to the Employee Management System.

The application can now export selected employee information into a file that can be opened using spreadsheet software.

## New Files

```text
Projects/employee_management_system/exporter.py
Projects/employee_management_system/test_exporter.py
```

## What CSV Means

CSV means:

```text
Comma-Separated Values
```

Example:

```csv
employee_id,name,department,position,salary
EMP004,Aki,wertt,qwqert,60000
EMP005,Ruth,SSS,Liason,50000
```

Each line represents one record, and commas separate the fields.

CSV files are useful because they can be opened by:

- Microsoft Excel
- Google Sheets
- LibreOffice Calc
- Text editors
- Python data-analysis tools

## Export File Location

```python
EXPORT_FILE = Path(__file__).with_name(
    "employee_report.csv"
)
```

This creates the report in the same folder as `exporter.py`.

Generated file:

```text
Projects/employee_management_system/employee_report.csv
```

## Export Function

```python
def export_employees_to_csv(
    employee_list,
    file_path=EXPORT_FILE,
):
    fieldnames = [
        "employee_id",
        "name",
        "department",
        "position",
        "salary",
    ]

    try:
        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(employee_list)

        return True

    except OSError as error:
        print()
        print("ERROR: Employee report could not be exported.")
        print(f"Details: {error}")
        return False
```

## Important CSV Components

### `csv.DictWriter`

```python
writer = csv.DictWriter(...)
```

Creates a CSV writer designed to receive Python dictionaries.

Dictionary keys become CSV columns.

### `fieldnames`

```python
fieldnames = [
    "employee_id",
    "name",
    "department",
    "position",
    "salary",
]
```

Controls which fields are exported and their column order.

Sensitive or unnecessary fields such as email and phone number are not included.

### `writer.writeheader()`

```python
writer.writeheader()
```

Writes the column headings:

```csv
employee_id,name,department,position,salary
```

### `writer.writerows()`

```python
writer.writerows(employee_list)
```

Writes all employee dictionaries as CSV rows.

### `extrasaction="ignore"`

```python
extrasaction="ignore"
```

Employee dictionaries contain more fields than the CSV report needs.

This option ignores fields not listed in `fieldnames`, including:

- Email
- Phone number
- Country
- Company
- Performance score

### `newline=""`

```python
newline=""
```

Prevents unwanted blank lines between CSV rows on Windows.

It does not remove ordinary spaces from employee data.

### `encoding="utf-8-sig"`

```python
encoding="utf-8-sig"
```

Improves compatibility with Excel and supports international characters.

## Success and Failure Results

The function returns:

```python
True
```

when the CSV file is exported successfully.

It returns:

```python
False
```

when an operating-system error prevents the file from being written.

This result does not indicate whether a particular employee exists.

## Application Menu Integration

The menu now contains:

```text
7. Export Employee Report
8. Exit
```

When option 7 is selected:

```python
export_successful = export_employees_to_csv(
    employees
)
```

If successful, the application displays the report location and records the export in `activity.log`.

## Protecting Generated Reports

The following path was added to `.gitignore`:

```gitignore
# Generated CSV reports
Projects/employee_management_system/employee_report.csv
```

The report contains employee names and salaries. Ignoring it prevents the generated business data from being accidentally committed or shared through Git.

The Python source code in `exporter.py` can be committed safely. The generated employee report remains local.

## Export Testing

`test_exporter.py` verifies:

- A CSV file can be created.
- Employee data is written correctly.
- Column headings are correct.
- Email information is excluded.
- An empty employee list still creates a valid CSV with headings.
- Temporary test files do not overwrite the real report.

## `TemporaryDirectory`

```python
with TemporaryDirectory() as temporary_directory:
```

Creates an isolated folder for the test.

Benefits:

- Does not overwrite the real employee report.
- Keeps test files separate from business data.
- Automatically deletes the temporary folder afterward.
- Allows the test to run repeatedly.

## Test Results

```text
Exporter tests:        2 passed
Reporting tests:       2 passed
Employee-system tests: 15 passed
Storage tests:         3 passed
```

Total:

```text
22 tests passed
```

The invalid-JSON message shown during storage testing is intentional. The test deliberately creates invalid JSON to verify safe error handling.

## Separation of Responsibilities

```text
exporter.py
    Converts employee dictionaries into CSV records.

main_refactored.py
    Provides the export menu option and user messages.

test_exporter.py
    Verifies export behavior using temporary files.

.gitignore
    Prevents generated employee reports from being committed.
```

## Key Lesson

Source code and generated business data should be treated differently.

The export logic is reusable source code and belongs in Git. The generated CSV contains local employee information and should normally remain outside Git.

## Day 25 Accomplishments

- Learned the CSV file format.
- Created `exporter.py`.
- Created `test_exporter.py`.
- Exported selected employee fields.
- Excluded email and phone details.
- Added export success and error handling.
- Added a new application menu option.
- Logged successful CSV exports.
- Protected the generated report with `.gitignore`.
- Passed all 22 automated tests.