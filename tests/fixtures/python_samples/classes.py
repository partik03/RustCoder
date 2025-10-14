"""Python class example."""


class Calculator:
    """A simple calculator."""
    
    def __init__(self, initial_value: int = 0):
        """Initialize calculator with optional initial value."""
        self.value = initial_value
    
    def add(self, n: int) -> int:
        """Add a number to current value."""
        self.value += n
        return self.value
    
    def subtract(self, n: int) -> int:
        """Subtract a number from current value."""
        self.value -= n
        return self.value
    
    def get_value(self) -> int:
        """Get current value."""
        return self.value


if __name__ == "__main__":
    calc = Calculator(10)
    print(calc.add(5))
    print(calc.subtract(3))
    print(calc.get_value())

