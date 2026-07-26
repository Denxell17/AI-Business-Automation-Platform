
# Exercise 1
count = 1

while count <= 5:
    print(f"count: {count}")
    count = count + 1
print("Loop Finished")

print()

# Exercise 2
for employee_number in range(1, 6):
    print(f"Processing Employee #{employee_number}")

print("All employees processed. ")

print()

# Exercise 3
for employee_number in range(1, 6):
    if employee_number == 3:
        print("Employee #3 Skipped.")
        continue
    print(f"Processing Employee #{employee_number}")

print("Processing Completed. ")

print()

# Exercise 4
while True:
    print("=" * 40)
    print("EMPLOYEE MANAGEMENT MENU".center(40))
    print("=" * 40)
    print("1. Register Employee")
    print("2. View Payroll")
    print("3. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        print("Register Employee Selected. ")
    elif choice == "2":
        print("View Payroll Selected")
    elif choice == "3":
        print("Closing the program...")
        break
    else:
        print("Invalid option. Please choose 1, 2, or 3.")

    print()

print("Program closed successfully.")


