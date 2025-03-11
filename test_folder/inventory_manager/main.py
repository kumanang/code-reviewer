from inventory import Inventory
from product import Product
from utils import validate_input

def main():
    """Main function to interact with the inventory system."""
    inventory = Inventory()

    # Adding some initial products
    inventory.add_product(Product("Laptop", "Electronics", 1000, 5))
    inventory.add_product(Product("Phone", "Electronics", 600, 10))
        inventory.add_product(Product("Notebook", "Stationery", 5, 50))

    while True:
        print("\nInventory Manager")
        print("1. List Products")
        print("2. Add Product")
        print("3. Sell Product")
        print("4. Show Total Inventory Value")
        print("5. Exit")

        choice = validate_input("Enter your choice: ", int)

        if choice == 1:
            inventory.list_products()
        elif choice == 2:
            name = input("Enter product name: ")
            category = input("Enter category: ")
            price = validate_input("Enter price: ", float)
            stock = validate_input("Enter stock quantity: ", int)
            inventory.add_product(Product(name, category, price, stock))
            print(f"{name} added to inventory!")
        elif choice == 3:
            name = input("Enter product name to sell: ")
            quantity = validate_input("Enter quantity: ", int)
            inventory.sell_product(name, quantity)
        elif choice == 4:
            print(f"Total Inventory Value: ${inventory.total_inventory_value():.2f}")
        elif choice == 5:
            print("Exiting program...")
            break
        else:
            print("Invalid choice! Please select a valid option.")

if __name__ == "__main__":
    main()
