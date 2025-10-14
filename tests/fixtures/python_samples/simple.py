"""Simple Python example."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def greet(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(add(5, 3))
    print(greet("World"))

