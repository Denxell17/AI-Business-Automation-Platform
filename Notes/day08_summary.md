# Day 8 Summary — Testing, Documentation, Security, and Git

## Goal

Review the Employee Management System, test its business rules, document the project, protect unnecessary or private files, and create the first Git commit.

## Topics Learned

- The Python main-program guard
- Importing functions safely
- Boundary testing
- Test files
- Project documentation
- `README.md`
- `.gitignore`
- Temporary Python files
- Virtual environments
- Environment variables
- API-key security
- Local Git repositories
- Git branches
- Untracked files
- Staging
- Commits
- Clean working trees

# Main-Program Guard

## The Original Problem

The application originally ended with:

```python
run_program()
```

This always started the interactive menu whenever Python loaded the file.

That behavior becomes a problem when another file wants to import only one function:

```python
from main_refactored import determine_performance
```

Without protection, importing the function would also start the entire Employee Management System menu.

## The Main Guard

The direct call was replaced with:

```python
if __name__ == "__main__":
    run_program()
```

This means:

> Run the application only when `main_refactored.py` is launched directly.

When another Python file imports its functions, the menu does not start automatically.

## Double Underscores

The correct names are:

```python
__name__
"__main__"
```

Each has two underscores before and two underscores after the word.

These are sometimes called “dunder” names:

```text
dunder = double underscore
```

Incorrect:

```python
if _name_ == "_main_":
```

Correct:

```python
if __name__ == "__main__":
    run_program()
```

## Why `run_program()` Is Indented

```python
if __name__ == "__main__":
    run_program()
```

The indentation means `run_program()` belongs to the `if` block.

It runs only when the condition is true.

# Automated Boundary Testing

## Test File

A separate test file was created:

```text
Projects/employee_management_system/test_performance.py
```

It imported the performance function:

```python
from main_refactored import determine_performance
```

Because of the main guard, importing the function did not open the menu.

## Test Scores

The test checked:

```python
test_scores = [-1, 0, 69, 70, 79, 80, 89, 90, 100, 101]
```

These values were chosen around important boundaries.

Expected results:

```text
 -1 → Invalid Score       → 0%
  0 → Needs Improvement  → 0%
 69 → Needs Improvement  → 0%
 70 → Good               → 5%
 79 → Good               → 5%
 80 → Very Good          → 10%
 89 → Very Good          → 10%
 90 → Outstanding        → 15%
100 → Outstanding        → 15%
101 → Invalid Score      → 0%
```

## Why Boundary Testing Matters

Bugs often occur where one category changes into another.

For example:

```text
69 → 70
79 → 80
89 → 90
100 → 101
```

Testing only a normal value such as `88` would not prove that the boundaries were correct.

## Test Loop

The test used a loop:

```python
for score in test_scores:
    rating, bonus_rate = determine_performance(score)

    print(
        f"Score: {score:>3} | "
        f"Rating: {rating:<18} | "
        f"Bonus: {bonus_rate:.0%}"
    )
```

This reused:

- Lists
- Loops
- Functions
- Multiple return values
- F-string formatting

# Project Documentation

## `README.md`

A `README.md` file was created in the project root:

```text
AI-Business-Automation-Platform/
└── README.md
```

The README explains:

- The project’s purpose
- Current features
- Technologies used
- Project structure
- How to run the application
- How to run tests
- Concepts practiced
- Future plans
- Current project status

## README Versus Notes

```text
README.md → introduction for employers, clients, and developers
Notes/    → detailed personal learning explanations
```

The README is concise and project-focused.

The Notes folder records what was learned each day.

## Markdown

The `.md` extension means Markdown.

Examples:

```markdown
# Main heading
## Smaller heading
- List item
```

Markdown formats plain text into readable documentation.

# The `.gitignore` File

## Purpose

`.gitignore` tells Git which files and folders it should not track.

It acts as a filter:

```text
Everything on the computer
→ .gitignore filters unwanted files
→ Git tracks meaningful project files
```

It does not delete or hide files.

## Python Temporary Files

Python created:

```text
__pycache__/
```

This folder contains compiled `.pyc` files that help Python load imported modules.

These files should not be committed because:

- Python creates them automatically.
- Python can recreate them.
- They are not source code.
- They create unnecessary repository clutter.

Ignore rules:

```gitignore
**/__pycache__/
**/*.pyc
**/*.pyo
```

The pattern:

```text
**/
```

means at any folder depth.

## Virtual Environments

Ignored:

```gitignore
venv/
.venv/
```

A virtual environment can contain thousands of installed package files specific to one computer.

Developers normally share a dependency list instead of uploading the complete environment.

## Environment Variables and Secrets

Ignored:

```gitignore
.env
```

A future `.env` file might contain private configuration:

```text
AI_API_KEY=private-value
DATABASE_PASSWORD=private-password
```

These values must not be uploaded publicly.

## API-Key Security

An API key works like a password that authorizes software to use a service.

If a paid API key is exposed, another person might use the service under the owner’s account. That usage could potentially be billed to the account.

Our project rule is:

```text
No paid API
No billing account
No credit card
No paid cloud service
```

The project will use free, local, or open-source options unless this rule is explicitly changed.

The current Employee Management System creates no API charges.

## Important `.gitignore` Limitation

`.gitignore` prevents untracked files from being added.

It does not automatically remove a file that Git is already tracking.

That is why the accidentally staged cache file had to be removed from staging:

```powershell
git rm -r --cached Projects/employee_management_system/__pycache__
```

The option:

```text
--cached
```

means:

> Remove it from Git’s tracking area but keep it on the computer.

# Git Fundamentals

## What Is Git?

Git is a version-control system.

It records changes to a project over time.

Git allows developers to:

- Save project snapshots
- Review changes
- Return to earlier versions
- Understand project history
- Collaborate with others

Git works locally and does not require payment.

## Git Versus GitHub

```text
Git     → version-control software on the computer
GitHub  → online service that can store Git repositories
```

The Day 8 work used local Git.

The project was not uploaded to GitHub.

# Initializing the Repository

The first status check returned:

```text
fatal: not a git repository
```

This meant Git was installed, but the project was not initialized.

The project was initialized using:

```powershell
git init -b main
```

This:

- Created a hidden `.git` folder
- Activated local version control
- Created a branch named `main`
- Did not upload anything

# Git Branch

The project uses:

```text
main
```

A branch is a line of development.

Later, separate branches can be used for new features without immediately changing the stable version.

# `git status`

The command:

```powershell
git status
```

inspects the current repository.

It can show:

- Current branch
- Untracked files
- Modified files
- Staged files
- Whether the project is clean

`git status` does not change files.

It is a safe command that should be used frequently.

# Untracked Files

After initialization, Git reported untracked files.

“Untracked” means:

> Git can see the file, but it has not been added to version history.

This is normal for a new repository.

Git did not display empty `Assets` and `Notes` folders because Git tracks files rather than empty folders.

Once the Notes folder contained summary files, Git could track it.

# Staging

Files were staged using:

```powershell
git add .
```

The period means:

> Stage all new and changed files in the current project, except ignored files.

Staging prepares files for the next commit.

Workflow:

```text
Working files
→ git add
→ Staging area
→ git commit
→ Local history
```

`git add` does not upload files.

# Reviewing Staged Files

After staging, this command was used again:

```powershell
git status
```

Reviewing the staged list found that a cache file had accidentally been included.

This demonstrated why developers should always inspect the staging area before committing.

Professional habit:

```text
Make changes
→ check status
→ stage files
→ check status again
→ commit
```

# Updating a Staged File

The `.gitignore` file was changed after its earlier version had already been staged.

Git therefore showed:

```text
Changes to be committed
```

and:

```text
Changes not staged for commit
```

The latest version was staged using:

```powershell
git add .gitignore
```

This replaced the staged copy with the newest saved version.

# First Commit

The first local snapshot was created with:

```powershell
git commit -m "Complete Sprint 1 employee management system"
```

The `-m` option supplies a commit message.

The message describes what the snapshot contains.

Result:

```text
Commit: f15626f
Files: 11
Lines added: 584
```

The term:

```text
root-commit
```

meant it was the first commit in the repository.

# What a Commit Is

A commit is a recorded snapshot of staged project files.

It helps answer:

- What changed?
- When did it change?
- Why was it changed?
- Which version was working?

A commit is local until it is pushed to an online repository.

# Clean Working Tree

The final status was:

```text
On branch main
nothing to commit, working tree clean
```

This meant:

- All intended changes were committed.
- No tracked files had changed afterward.
- Nothing was waiting in the staging area.
- The local project history was current.

# Git Workflow to Remember

```text
1. Edit and save files
2. Run git status
3. Review the changes
4. Run git add
5. Run git status again
6. Run git commit
7. Run git status one final time
```

Important commands:

```powershell
git status
git add .
git add filename
git commit -m "Describe the change"
```

# Day 8 Accomplishments

- Added the Python main guard
- Imported application functions safely
- Created a separate performance test
- Tested rating boundaries
- Created project documentation
- Corrected `README.md` from a folder into a file
- Created `.gitignore`
- Ignored cache and private configuration files
- Learned why secrets must not be committed
- Established a zero-cost AI rule
- Initialized a local Git repository
- Created the `main` branch
- Reviewed untracked and staged files
- Removed an unwanted cache file from staging
- Created the first local Git commit
- Confirmed a clean working tree

# Important Things to Remember

```text
if __name__ == "__main__":
    run_program()
```

means:

> Run the application only when this file is launched directly.

```text
README.md  → explains the project
Notes/     → records daily learning
.gitignore → filters unwanted or private files
```

Git commands:

```text
git status → inspect the repository
git add    → prepare files
git commit → record a local snapshot
```

Security rules:

```text
Source code        → may be committed
Documentation      → may be committed
Tests              → may be committed
Temporary files    → should be ignored
Passwords and keys → must never be committed
```

# Personal Reflection

Day 8 transformed the Employee Management System from working code into a documented, tested, safer, and version-controlled software project. The work introduced professional habits that will protect and organize every future stage of the AI Business Automation Platform.