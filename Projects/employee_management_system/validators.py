def get_positive_integer(
    prompt: str,
    field_name: str,
) -> int:
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



def get_integer_in_range(
    prompt: str,
    field_name: str,
    minimum: int,
    maximum: int,
) -> int:
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


            
def get_required_text(
    prompt: str,
    field_name: str,
) -> str:
    while True:
        value = input(prompt).strip()

        if value:
            return value

        print(f"{field_name} cannot be blank.")