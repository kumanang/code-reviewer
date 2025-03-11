from product import Product

class Inventory:
    """Manages a collection of products."""

    def __init__(self):
        self.products = []

    def add_product(self, product: Product):
        """Adds a new product to inventory."""
        self.products.append(product)

    def list_products(self):
        """Lists all available products."""
        if not self.products:
            print("No products in inventory!")
            return
        for product in self.products:
            print(product)

    def sell_product(self, product_name: str, quantity: int):
        """Sells a product if available in stock."""
        for product in self.products:
            if product.name.lower() == product_name.lower():
                if product.update_stock(-quantity):
                    print(f"Sold {quantity} unit(s) of {product_name}")
                return
        print(f"Product '{product_name}' not found!")

    def total_inventory_value(self):
        """Calculates the total value of the inventory."""
        return sum(p.price * p.stock for p in self.products)
