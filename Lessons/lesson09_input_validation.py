def get_positive_integer(prompt, field_name): # Function code.
    while True:
        try:
            value = int(input(prompt))

            if value <= 0:
                print(f"{field_name} must be greater than zero.")
                continue

            return value

        except ValueError:
            print(f"Invalid {field_name}. Please enter a whole number.")


def get_integer_in_range(                   # Function code.
        prompt,
        field_name,
        minimum,
        maximum
):
    while True:
        try:
            value = int(input(prompt))

            if minimum <= value <= maximum:
                return value

            print(
                f"{field_name} must be between "
                f"{minimum} and {maximum}."
            )

        except ValueError:
            print(
                f"Invalid {field_name}. "
                "Please enter a whole number."
            )


def get_required_text(prompt, field_name):
    while True:
        value = input(prompt).strip()

        if value:
            return value

        print(f"{field_name} cannot be blank.")


name = get_required_text(
    "Enter Employee Name: ",
    "Employee name"
)

salary = get_positive_integer(
    "Enter Monthly Salary: ",
    "Salary"
)

years_of_experience = get_integer_in_range(
    "Enter Years of Experience: ",
    "Years of Experience",
    0,
    60
)

performance_score = get_integer_in_range(
    "Enter Performance Score (0-100): ",
    "Performance Score",
    0,
    100
)

print()
print(f"Accepted Employee Name: {name}")
print(f"Accepted Salary: ₱{salary:,.2f}")
print(f"Accepted Experience: {years_of_experience} years")
print(
    f"Accepted Performance Score: "
    f"{performance_score}"
)