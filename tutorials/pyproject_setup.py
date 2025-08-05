#!/usr/bin/env python3
"""Tutorial: Setting up pyproject.toml for MyPy."""

from typing import List, Optional, Dict
from .base_tutorial import BaseTutorial, Question


class PyprojectSetupTutorial(BaseTutorial):
    """Tutorial for setting up pyproject.toml configuration."""
    
    @property
    def id(self) -> str:
        """Unique identifier for this tutorial."""
        return "pyproject_setup"  # Override to match registry key
    
    @property
    def related_errors(self) -> List[str]:
        """List of MyPy error codes this tutorial helps with."""
        return ["config-error", "import-untyped"]
    
    @property
    def title(self) -> str:
        """Display title of the tutorial."""
        return "Setting Up pyproject.toml for Type Checking"
    
    @property
    def description(self) -> str:
        """Brief description of what this tutorial covers."""
        return "Learn how to configure MyPy and Python projects with pyproject.toml"
    
    @property
    def difficulty(self) -> int:
        """Difficulty level from 1-5."""
        return 1  # Configuration is a basic setup task
    
    @property
    def estimated_minutes(self) -> int:
        """Estimated time to complete in minutes."""
        return 10
    
    @property
    def pages(self) -> List[str]:
        """List of tutorial pages (3-5 pages of content)."""
        return [
            # Page 1: Introduction to pyproject.toml
            """# Understanding pyproject.toml

`pyproject.toml` is a configuration file used by Python packaging tools and other 
development tools like linters, formatters, and type checkers.

## The Three Main Tables

**[project]** - Basic metadata about your project
- Used by most build backends
- Contains name, version, dependencies, author info, etc.

**[tool]** - Tool-specific configurations
- Has subtables like [tool.mypy], [tool.black], [tool.pytest]
- Each tool defines its own configuration options

**[build-system]** - Build backend configuration
- Specifies which tools build your package

This tutorial will help you understand and create your pyproject.toml!""",
            
            # Page 2: Basic Information - Name and Version
            """# Project Name and Version

## The `name` Field

The project name is **required** and the only field that cannot be marked as dynamic:

```toml
[project]
name = "spam_eggs"  # Use underscores for MyPy compatibility
```

**Naming Rules:**
- Must use ASCII letters, digits, underscores `_`, hyphens `-`, and periods `.`
- Cannot start or end with underscore, hyphen, or period
- PyPI treats these as equivalent: `cool-stuff` = `Cool-Stuff` = `cool.stuff` = `COOL_STUFF`

⚠️ **Important MyPy Restriction:**
While PyPI accepts hyphens in package names, MyPy requires underscores!
- ✅ Good for MyPy: `storm_checker`, `my_awesome_package`
- ❌ Bad for MyPy: `storm-checker`, `my-awesome-package`

If you use hyphens, MyPy will error with: "package-name is not a valid Python package name"

## The `version` Field

Specifies your project version:

```toml
[project]
version = "2020.0.0"
```

Can be marked as dynamic for automatic versioning:

```toml
[project]
dynamic = ["version"]
```

This allows getting version from `__version__` or Git tags.""",
            
            # Page 3: Essential MyPy Configuration Settings
            """# Essential MyPy Configuration Settings

## Platform & Environment Configuration

```toml
[tool.mypy]
python_version = "3.10"        # Target Python version
platform = "linux"             # Target platform (optional)
mypy_path = "src:stubs"        # Additional module search paths
```

## Strictness Levels (Start Gradual)

```toml
# Basic strictness - good starting point
check_untyped_defs = false     # Check function bodies even without annotations
disallow_untyped_defs = false  # Require annotations on function definitions
strict_optional = true         # Treat Optional[T] and T | None strictly

# Import handling
ignore_missing_imports = true  # Don't error on missing stubs
follow_imports = "normal"      # Follow imports and type-check them
```

## Error Display & Reporting

```toml
pretty = false                 # Must be false for stormchecker compatibility
show_error_codes = true        # Show error codes like [attr-defined]
show_error_context = true      # Show source code context for errors
color_output = true            # Colorize terminal output
error_summary = true           # Show error summary at end
```

These settings provide a solid foundation while keeping MyPy approachable!""",
            
            # Page 4: Advanced Configuration & Per-Module Settings
            """# Advanced Configuration & Per-Module Settings

## Advanced Type Checking Options

```toml
[tool.mypy]
# Advanced strictness
warn_return_any = true         # Warn when returning Any from typed function
warn_unused_ignores = true     # Warn about unnecessary # type: ignore
warn_redundant_casts = true    # Warn about unnecessary casts
warn_unreachable = true        # Warn about unreachable code

# Additional checks
disallow_any_generics = false  # Disallow Any in generic types (strict)
disallow_subclassing_any = true # Disallow subclassing Any
warn_incomplete_stub = true     # Warn about incomplete stub files
```

## Per-Module Configuration with [[tool.mypy.overrides]]

```toml
# Strict settings for main source code
[[tool.mypy.overrides]]
module = "myproject.*"
disallow_untyped_defs = true
strict_optional = true
warn_return_any = true

# Lenient settings for tests
[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true
disallow_untyped_defs = false

# Handle third-party packages
[[tool.mypy.overrides]]
module = ["requests.*", "pandas.*"]
ignore_missing_imports = true
```

This gives you fine-grained control over type checking across your project!""",
            
            # Page 5: Common MyPy Error Patterns & Solutions
            """# Common MyPy Error Patterns & Solutions

Understanding frequent MyPy errors helps you configure and fix issues faster:

## Import-Related Errors

**Error:** `Cannot find implementation or library stub for module named 'requests'`
**Solution:** Add to overrides:
```toml
[[tool.mypy.overrides]]
module = "requests.*"
ignore_missing_imports = true
```

## Function Annotation Errors

**Error:** `Function is missing a return type annotation`
**Solution:** Either add return type or use:
```toml
disallow_untyped_defs = false  # During migration
```

## Optional/None Handling

**Error:** `Argument 1 has incompatible type "None"; expected "str"`
**Solution:** Use proper Optional handling:
```toml
strict_optional = true  # Enforces proper None checking
no_implicit_optional = false  # Start lenient
```

## Gradual Migration Strategy

1. Start with `ignore_missing_imports = true`
2. Fix import errors module by module using overrides
3. Gradually enable stricter settings per module
4. Use `# type: ignore` sparingly for complex cases

The key is incremental progress, not perfection overnight!

## What's Next?

Practice by creating a pyproject.toml for your project and gradually improving your type checking configuration!"""
        ]
    
    @property
    def questions(self) -> Dict[int, Question]:
        """Questions to test understanding."""
        return {
            1: Question(  # After page 2 (Name and Version)
                text="Which package name would cause problems with MyPy type checking?",
                options=[
                    "my_awesome_tool",
                    "my-awesome-tool",
                    "MyAwesomeTool",
                    "my_awesome_tool_v2"
                ],
                correct_index=1,
                explanation="MyPy requires package names to use underscores, not hyphens. While 'my-awesome-tool' works fine with PyPI, MyPy will error with 'my-awesome-tool is not a valid Python package name'. Always use underscores for MyPy compatibility.",
                hint="Remember that MyPy has stricter naming requirements than PyPI..."
            ),
            2: Question(  # After page 3 (Essential MyPy Configuration)
                text="What is the recommended approach for MyPy strictness when starting a new project?",
                options=[
                    "Start with strict=true for maximum safety",
                    "Begin with lenient settings and gradually increase strictness",
                    "Use disallow_untyped_defs=true from day one",
                    "Always use ignore_missing_imports=false"
                ],
                correct_index=1,
                explanation="Starting with lenient settings like ignore_missing_imports=true and check_untyped_defs=false allows gradual adoption without overwhelming new users with errors.",
                hint="What makes type checking adoption easier for teams?"
            ),
            3: Question(  # After page 4 (Advanced Configuration)
                text="What does [[tool.mypy.overrides]] allow you to do?",
                options=[
                    "Override Python's built-in type system",
                    "Apply different MyPy settings to specific modules or packages",
                    "Create custom error messages for type violations",
                    "Automatically fix type errors in your code"
                ],
                correct_index=1,
                explanation="[[tool.mypy.overrides]] sections let you apply different MyPy configurations to specific modules, allowing strict settings for your code and lenient ones for tests or third-party packages.",
                hint="Think about how you might want different rules for different parts of your project..."
            ),
            4: Question(  # After page 5 (Error Patterns & Solutions - Final knowledge check)
                text="Which combination of settings would be BEST for a production codebase that's ready for strict type checking?",
                options=[
                    "ignore_missing_imports=true, check_untyped_defs=false",
                    "disallow_untyped_defs=true, warn_return_any=true, strict_optional=true", 
                    "ignore_errors=true, follow_imports='skip'",
                    "pretty=false, show_error_codes=false"
                ],
                correct_index=1,
                explanation="For production code, you want strict settings: disallow_untyped_defs=true ensures all functions have type annotations, warn_return_any=true catches loose Any types, and strict_optional=true enforces proper None handling.",
                hint="Which settings would catch the most type-related bugs in production?"
            )
        }
    
    @property
    def practice_exercise(self) -> Optional[str]:
        """Optional practice exercise for hands-on learning."""
        return """Create a pyproject.toml for your project with:
1. Basic MyPy configuration
2. Your project name and version
3. Python version requirement

Then run 'stormcheck mypy' to see the difference!"""