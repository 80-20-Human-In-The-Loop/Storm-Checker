#!/usr/bin/env python3
"""
Type Annotations Basics Tutorial
================================
Learn the fundamentals of Python type annotations and how they improve code quality.
"""

from typing import Dict
from cli.user_input.multiple_choice import Question
from .base_tutorial import BaseTutorial


class TypeAnnotationsBasics(BaseTutorial):
    """Tutorial teaching basic type annotation concepts."""
    
    @property
    def id(self) -> str:
        """Unique identifier for this tutorial."""
        return "type_annotations_basics"  # Override to match registry key
    
    @property
    def title(self) -> str:
        return "Type Annotations Basics"
        
    @property
    def description(self) -> str:
        return "Learn how to add type hints to variables and functions for better code clarity and error prevention."
        
    @property
    def pages(self) -> list[str]:
        # Enhanced 7-slide tutorial structure
        page1 = """# Introduction to Type Annotations

Type annotations (type hints) tell Python and tools like MyPy what types your code expects, enabling powerful error detection and better development experience.

## Before Type Annotations
```python
def calculate_tax(price, rate):
    return price * rate

# What types? What if someone passes strings?
result = calculate_tax("100", "0.1")  # Runtime error!
```

## With Type Annotations
```python
def calculate_tax(price: float, rate: float) -> float:
    return price * rate

# MyPy catches this before you run the code!
result = calculate_tax("100", "0.1")  # Error: Argument has incompatible type
```

## Why Type Annotations Matter

**🐛 Catch Bugs Early**: MyPy finds type errors before runtime
**📚 Self-Documenting**: Code clearly shows expected types
**⚡ Better IDE Support**: Smart autocomplete and refactoring
**🔧 Easier Maintenance**: Understand code intent months later

Type annotations are optional but become essential for larger codebases!"""

        page2 = """# Basic Variable Type Annotations

Python lets you annotate variables to specify their expected types, helping MyPy catch mistakes and improving code clarity.

## Built-in Types
```python
# Basic types
name: str = "Alice"
age: int = 30
is_active: bool = True
height: float = 5.9

# Annotation without immediate assignment
user_id: int  # Declare type first
user_id = 12345  # Assign value later
```

## Collection Types
```python
# Lists with specific element types
names: list[str] = ["Alice", "Bob", "Charlie"]
numbers: list[int] = [1, 2, 3, 4, 5]

# Dictionaries with key and value types
scores: dict[str, int] = {"Alice": 95, "Bob": 87}
config: dict[str, bool] = {"debug": True, "cache": False}

# Tuples with fixed structure
coordinates: tuple[float, float] = (10.5, 20.3)
rgb_color: tuple[int, int, int] = (255, 128, 0)

# Sets
tags: set[str] = {"python", "typing", "mypy"}
```

## Common MyPy Issue: Empty Collections
```python
# This causes a 'var-annotated' error in strict mode
users = []  # MyPy can't infer type!

# Fix: Add explicit type annotation
users: list[str] = []  # Clear!
```

**🔧 For Python 3.8 and earlier**: Import from typing module
`from typing import List, Dict, Tuple, Set`"""

        page3 = """# Function Type Annotations

Function annotations specify types for parameters and return values, helping MyPy catch `no-untyped-def` and `no-untyped-call` errors.

## Basic Function Annotations
```python
def add_numbers(x: int, y: int) -> int:
    return x + y

def format_name(first: str, last: str) -> str:
    return f"{first} {last}"

def is_valid_email(email: str) -> bool:
    return "@" in email and "." in email
```

## Functions That Don't Return Values
```python
def log_message(message: str) -> None:
    print(f"[LOG] {message}")

def save_to_file(data: str, filename: str) -> None:
    with open(filename, "w") as f:
        f.write(data)
```

## Functions With Optional Parameters
```python
def greet_user(name: str, prefix: str = "Hello") -> str:
    return f"{prefix}, {name}!"

def create_user(name: str, age: int, email: Optional[str] = None) -> dict[str, str | int]:
    user = {"name": name, "age": age}
    if email:
        user["email"] = email
    return user
```

## Complex Return Types
```python
def get_user_scores(user_id: int) -> list[dict[str, int]]:
    return [{"test_1": 95}, {"test_2": 87}]

def parse_config() -> tuple[str, int, bool]:
    return ("localhost", 8080, True)
```

**⚠️ MyPy Error Prevention**: Always annotate both parameters AND return types to avoid `no-untyped-def` errors!"""

        page4 = """# Advanced Type Patterns

Advanced type annotations help you express complex requirements and handle real-world scenarios more precisely.

## Union Types: Multiple Possible Types
```python
# Python 3.10+ syntax
def process_id(user_id: int | str) -> str:
    return str(user_id)

# Older Python versions
from typing import Union
def process_id(user_id: Union[int, str]) -> str:
    return str(user_id)
```

## Optional Types: Values That Can Be None
```python
# Modern way (Python 3.10+)
def find_user(email: str) -> dict[str, str] | None:
    if email in users:
        return users[email]
    return None

# Traditional way
from typing import Optional
def find_user(email: str) -> Optional[dict[str, str]]:
    # Same as dict[str, str] | None
    return users.get(email)
```

## Literal Types: Exact Values
```python
from typing import Literal

def set_log_level(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> None:
    # Only these exact strings are allowed!
    configure_logging(level)

def get_http_method() -> Literal["GET", "POST", "PUT", "DELETE"]:
    return "GET"
```

## Type Aliases: Readable Complex Types
```python
# Create readable names for complex types
UserId = int
UserData = dict[str, str | int | bool]
APIResponse = dict[str, str | list[UserData]]

def get_user_info(user_id: UserId) -> UserData:
    return {"name": "Alice", "age": 30, "active": True}

def fetch_users() -> APIResponse:
    return {"status": "success", "users": [get_user_info(1)]}
```

**💡 Pro Tip**: Use Union and Optional types to handle real-world data that might have multiple formats!"""

        page5 = """# Generic Types and Advanced Collections

Generic types and protocols enable flexible, reusable code while maintaining type safety.

## Generic Functions with TypeVar
```python
from typing import TypeVar, Optional

T = TypeVar('T')  # Generic type variable

def get_first_item(items: list[T]) -> Optional[T]:
    # Works with any list type!
    return items[0] if items else None

# Usage examples:
first_name: Optional[str] = get_first_item(["Alice", "Bob"])  # Optional[str]
first_number: Optional[int] = get_first_item([1, 2, 3])      # Optional[int]
```

## Complex Nested Collections
```python
# Database query results
QueryResult = list[dict[str, str | Optional[int]]]

def execute_query(sql: str) -> QueryResult:
    return [{"id": 1, "name": "Alice", "age": None}]

# Configuration with nested structure
AppConfig = dict[str, dict[str, str | int | bool]]

def load_config() -> AppConfig:
    return {
        "database": {"host": "localhost", "port": 5432, "ssl": True},
        "api": {"timeout": 30, "debug": False}
    }
```

## Callable Types: Function Annotations
```python
from typing import Callable

# Function that takes another function as parameter
def apply_to_list(items: list[int], func: Callable[[int], int]) -> list[int]:
    return [func(item) for item in items]

def double(x: int) -> int:
    return x * 2

# Usage
result = apply_to_list([1, 2, 3], double)  # [2, 4, 6]
```

## Protocol: Duck Typing with Structure
```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

def render_shape(shape: Drawable) -> None:
    shape.draw()  # Any object with draw() method works!

class Circle:
    def draw(self) -> None:
        print("Drawing circle")

render_shape(Circle())  # Works! Circle has draw() method
```

**🎯 Power of Generics**: Write once, work with any type while keeping type safety!"""

        page6 = """# MyPy Error Patterns and Solutions

Understanding and fixing common MyPy errors helps you adopt type annotations successfully.

## Error: no-untyped-def
**Problem**: Function missing type annotations
```python
# MyPy Error: Function is missing a type annotation [no-untyped-def]
def calculate_total(items):
    return sum(item.price for item in items)
```

**Solution**: Add complete type annotations
```python
def calculate_total(items: list['Item']) -> float:
    return sum(item.price for item in items)
```

## Error: no-untyped-call
**Problem**: Calling untyped function from typed code
```python
def process_data(data: list[str]) -> None:
    # Error: Call to untyped function "legacy_parser" [no-untyped-call]
    result = legacy_parser(data)

def legacy_parser(data):  # No annotations!
    return data
```

**Solution**: Add type annotations to called functions
```python
def legacy_parser(data: list[str]) -> list[str]:
    return data
```

## Error: var-annotated
**Problem**: Empty containers need explicit types
```python
# Error: Need type annotation for "users" [var-annotated]
users = []  # MyPy can't infer the type!
users.append("Alice")
```

**Solution**: Add explicit type annotation
```python
users: list[str] = []  # Clear type!
users.append("Alice")
```

## Quick Fixes
```python
# Use # type: ignore for temporary fixes (not recommended long-term)
legacy_result = old_function()  # type: ignore

# Use Any for truly dynamic types (use sparingly)
from typing import Any
dynamic_data: Any = json.loads(response)
```

**🔧 Pro Tip**: Start with basic annotations and gradually add more specificity!"""

        page7 = """# Best Practices and Real-World Integration

Successful type annotation adoption requires understanding when and how to use them effectively.

## Practical Type Annotation Strategy

**🥇 Start Simple**: Begin with obvious types
```python
# Start here
def get_user_name(user_id: int) -> str:
    return users[user_id].name

# Not here (too complex initially)
def process_data(data: dict[str, list[tuple[str, int]]]) -> ...
```

**🥈 Add Gradually**: Expand coverage over time
```python
# Phase 1: Basic functions
def calculate_tax(price: float) -> float: ...

# Phase 2: More complex patterns
def get_users() -> list[dict[str, str | int]]: ...

# Phase 3: Advanced generics
def cache_result[T](func: Callable[[], T]) -> T: ...
```

## Real-World Example: E-commerce Order System
```python
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: float

    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price

@dataclass
class Order:
    id: str
    items: list[OrderItem]
    status: OrderStatus
    created_at: datetime
    customer_email: str

    def calculate_total(self) -> float:
        return sum(item.total_price for item in self.items)

class PaymentProcessor(Protocol):
    def process_payment(self, amount: float) -> bool: ...

def process_order(order: Order, payment: PaymentProcessor) -> bool:
    total = order.calculate_total()
    if payment.process_payment(total):
        order.status = OrderStatus.CONFIRMED
        return True
    return False
```

## Integration with Development Workflow

**🔧 MyPy Integration**: `mypy --strict myproject/`
**📝 IDE Support**: VS Code, PyCharm automatically use type hints
**🧪 Testing**: Type annotations help catch test issues early
**📚 Documentation**: Types serve as living documentation

**Remember**: Type annotations are a journey, not a destination. Start small and build up!"""

        return [page1, page2, page3, page4, page5, page6, page7]
        
    @property 
    def questions(self) -> Dict[int, Question]:
        return {
            1: Question(  # After page 2 (Basic Variable Annotations)
                text="Which of these correctly annotates an empty list that will contain user names?",
                options=[
                    "names = []",
                    "names: list = []",
                    "names: list[str] = []",
                    "names: List(str) = []"
                ],
                correct_index=2,
                explanation="Empty collections need explicit type annotations. 'list[str]' tells MyPy this list will contain strings, preventing 'var-annotated' errors.",
                hint="MyPy needs to know what type of elements the list will contain..."
            ),
            2: Question(  # After page 3 (Function Type Annotations)
                text="What's the best type annotation for a function that returns either a User object or None?",
                options=[
                    "-> User | None",
                    "-> Optional[User]",
                    "-> Union[User, None]",
                    "All of the above are equivalent"
                ],
                correct_index=3,
                explanation="All three options are equivalent! 'User | None' (Python 3.10+), 'Optional[User]', and 'Union[User, None]' all represent the same type.",
                hint="Different syntax, same meaning..."
            ),
            3: Question(  # After page 4 (Advanced Type Patterns)
                text="You get a 'no-untyped-call' error when calling process_data() from your typed code. What's the issue?",
                options=[
                    "The process_data() function has no type annotations",
                    "You're passing the wrong type of argument",
                    "MyPy is configured incorrectly",
                    "The function returns the wrong type"
                ],
                correct_index=0,
                explanation="The 'no-untyped-call' error occurs when typed code calls a function that has no type annotations. Add type annotations to process_data() to fix it.",
                hint="The error name gives you a clue about what's missing..."
            ),
            4: Question(  # After page 5 (Generic Types)
                text="You're building a data processing pipeline. Which approach demonstrates the best type annotation practices?",
                options=[
                    "def process(data): return [x*2 for x in data]  # Keep it simple",
                    "def process(data: Any) -> Any: return [x*2 for x in data]  # Use Any for flexibility",
                    "def process[T: int | float](data: list[T]) -> list[T]: return [x*2 for x in data]  # Generic with constraints",
                    "def process(data: list[int | float]) -> list[int | float]: return [x*2 for x in data]  # Specific union type"
                ],
                correct_index=2,
                explanation="Option C uses modern generic syntax with type constraints, making the function reusable while maintaining type safety. It works with both int and float inputs while preserving the exact input type in the output.",
                hint="Think about reusability, type safety, and modern Python features..."
            ),
            6: Question(  # After page 7 (Best Practices) - FINAL COMPREHENSIVE QUESTION
                text="Your team is migrating a legacy codebase to use type annotations. What's the BEST strategy?",
                options=[
                    "Add 'Any' type to everything first, then gradually make types more specific",
                    "Start with critical business logic functions, add simple types, then expand coverage",
                    "Enable strict MyPy mode immediately to find all issues at once",
                    "Only annotate public APIs and leave internal functions untyped"
                ],
                correct_index=1,
                explanation="Starting with critical business logic and simple types allows gradual adoption without overwhelming the team. This approach provides immediate value while building momentum for broader type coverage.",
                hint="Consider team adoption, immediate value, and sustainable progress..."
            )
        }
        
    @property
    def estimated_minutes(self) -> int:
        return 15  # 7 slides, comprehensive coverage
        
    @property
    def difficulty(self) -> int:
        return 1
        
    @property
    def related_errors(self) -> list[str]:
        return ["no-untyped-def", "no-untyped-call", "var-annotated", "union-attr", "misc", "operator"]