def running_total():
    total = 0
    numbers = []  # List to store entered numbers

    while True:
        user_input = input("Enter a number (or type 'exit' to stop): ").strip()

        if user_input.lower() == "exit":
            print(f"\nNumbers entered: {numbers}")
            print(f"Final total: {total}")
            break

        try:
            number = float(user_input)
            numbers.append(number)  # Store the number in the list
            total += number
            print(f"Running total: {total}")
        except ValueError:
            print("Invalid input. Please enter a number.")

running_total()
