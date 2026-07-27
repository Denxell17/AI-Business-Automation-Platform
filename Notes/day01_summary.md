# Day 1 Summary — Project Setup and First Python Program

## Goal

Prepare the development environment, organize the project, and run the first Python program.

## Topics Learned

- Python
- Visual Studio Code
- Project folders and files
- Python `.py` files
- The terminal
- The `print()` function
- Running a Python program

## Development Tools

### Python

Python is the programming language used to build the application.

A Python source-code file ends with:

```text
.py
```

Example:

```text
lesson01_hello.py
```

### Visual Studio Code

Visual Studio Code is the editor used to:

- Create folders and files
- Write Python code
- Run programs
- View errors
- Use the terminal
- Work with Git

### Terminal

The terminal accepts commands and displays program output.

The prompt identifies the current folder:

```text
PS C:\Users\user\OneDrive\Documents\Projects\AI-Business-Automation-Platform>
```

Commands entered at this location run relative to the main project folder.

## Project Organization

The project was organized like this:

```text
AI-Business-Automation-Platform/
├── Assets/
├── Lessons/
├── Notes/
├── Projects/
└── README.md
```

### `Assets`

Stores supporting materials such as:

- Images
- Sample documents
- PDFs
- Spreadsheet files
- Future application resources

### `Lessons`

Stores code written while learning individual Python concepts.

Example:

```text
lesson01_hello.py
```

### `Notes`

Stores daily summaries, explanations, questions, and reflections.

### `Projects`

Stores the applications built using the concepts learned in the lessons.

### `README.md`

Documents the project’s purpose, features, structure, and instructions.

## Folders Versus Files

A folder organizes files and other folders.

Examples:

```text
Lessons/
Notes/
Projects/
```

A file contains information or code.

Examples:

```text
lesson01_hello.py
README.md
```

The `/` symbol after a name usually indicates a folder:

```text
Lessons/
```

The extension usually identifies a file:

```text
.py  → Python source-code file
.md  → Markdown documentation file
```

## First Python Program

The first program displayed project information:

```python
print("=" * 40)
print("AI BUSINESS AUTOMATION PLATFORM")
print("=" * 40)

print()

print("Developer: Dennis")
print("Version: 1.0")
print("Mission: Become an AI Automation Engineer")
```

## Understanding `print()`

`print()` is a built-in Python function.

Its purpose is to display information in the terminal:

```python
print("Hello")
```

Output:

```text
Hello
```

An empty `print()` creates a blank line:

```python
print()
```

This helps organize console output.

## String Multiplication

This code:

```python
print("=" * 40)
```

repeats the `=` character 40 times.

Output:

```text
========================================
```

This technique creates headings and separators for console applications.

## Running the Program

The program was run from the main project folder:

```powershell
python Lessons\lesson01_hello.py
```

On some Windows installations, this command can also work:

```powershell
py Lessons\lesson01_hello.py
```

The command tells Python:

1. Open the `Lessons` folder.
2. Find `lesson01_hello.py`.
3. Execute its instructions.
4. Display the results in the terminal.

## File-Naming Practice

Descriptive filenames are better than vague names.

Good examples:

```text
lesson01_hello.py
employee_profile.py
salary_calculator.py
```

Avoid vague names such as:

```text
test.py
new.py
practice.py
```

A descriptive filename explains the file’s purpose.

## Why Project Organization Matters

A small project may contain only a few files, but a business application can eventually contain hundreds.

Organizing the project early makes it easier to:

- Find files
- Review lessons
- Separate practice from application code
- Add future features
- Work with other developers
- Present the project professionally

## Day 1 Accomplishments

- Prepared Python and Visual Studio Code
- Opened the main project folder
- Created the initial folder structure
- Created the first Python file
- Used `print()`
- Displayed formatted output
- Ran Python from the terminal
- Started the AI Business Automation Platform

## Important Things to Remember

```text
Python             → programming language
VS Code            → code editor
Terminal           → runs commands and programs
.py                → Python file
.md                → Markdown documentation file
print()            → displays information
print() empty      → displays a blank line
folder             → organizes files
```

## Personal Reflection

Day 1 established the foundation of the AI Business Automation Platform. The project began as a simple console program, but its structure will support future employee management, automation, databases, web features, and local AI capabilities.
