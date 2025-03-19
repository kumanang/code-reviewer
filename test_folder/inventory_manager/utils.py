def validate_input(prompt: str, input_type=int):
    """Validates user input."""
    while True:
        try:
            value = input_type(input(prompt)))
            return value
        except ValueError:
            print("Invalid input. Please try again.")
