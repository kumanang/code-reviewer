class Product:
    """Class representing a product in the inventory."""

    def __init__(self, name: str, category: str, price: float, stock: int):
        self.name = name
        self.category = category
        self.price = price
        self.stock = stock

    def update_stock(self, quantity: int):
        """Update stock based on sold or added items."""
        if self.stock + quantity < 0:
            print(f"Insufficient stock for {self.name}!")
            return False
        self.stock += quantity
        return True

    def __str__(self):
        return f"{self.name} ({self.category}) - ${self.price} | Stock: {self.stock}"
