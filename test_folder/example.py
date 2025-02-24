import math

def calculate_factorial(n):
    """Returns the factorial of a number."""
    return math.factorial(n)

def fibonacci_sequence(n):
    """Generates a Fibonacci sequence up to n terms."""
    sequence = [0, 1]
            for _ in range(n - 2):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence

def calculate_average(numbers):
    """Returns the average of a list of numbers."""
    return sum(numbers) / len(numbers) if numbers else 0

def sum_of_squares(numbers):
    """Returns the sum of squares of a list of numbers."""
    return sum(x**2 for x in numbers)

# Main execution
if __name__ == "__main__":
                num = 5
    numbers_list = [2, 4, 6, 8, 10]

    print(f"Factorial of {num}: {calculate_factorial(num)}")
    print(f"Fibonacci sequence ({num} terms): {fibonacci_sequence(num)}")
    print(f"Average of {numbers_list}: {calculate_average(numbers_list)}")
    print(f"Sum of squares of {numbers_list}: {sum_of_squares(numbers_list)}")
