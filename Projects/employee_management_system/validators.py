def get_positive_integer(prompt, field_name):
    while True:
        try:
            value = int(input(prompt))
            if value <= 0:
                print(f"{field_name} must be greater than zero.")
                continue

            return value

        except ValueError:
            print(
                f"Invalid {field_name}. "
                "Please enter a whole number."
            )



def get_integer_in_range(prompt, field_name, minimum, maximum):
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