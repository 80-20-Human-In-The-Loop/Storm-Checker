"""
Shared Test Utilities
=====================
Common utilities for Storm Checker tests.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import json
import tempfile
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storm_checker.logic.mypy_runner import MypyError, MypyResult


class TestFileBuilder:
    """Build test Python files with various scenarios."""
    
    @staticmethod
    def create_clean_file() -> str:
        """Create a Python file with no type errors."""
        return '''
"""Clean Python file with proper type annotations."""

from typing import List, Optional, Dict, Union


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def process_list(items: List[str]) -> List[str]:
    """Process a list of strings."""
    return [item.upper() for item in items]


class DataProcessor:
    """Process data with type safety."""
    
    def __init__(self, name: str) -> None:
        self.name = name
        self.data: List[int] = []
        
    def add_value(self, value: int) -> None:
        """Add a value to the data."""
        self.data.append(value)
        
    def get_average(self) -> Optional[float]:
        """Calculate average of data."""
        if not self.data:
            return None
        return sum(self.data) / len(self.data)
'''

    @staticmethod
    def create_file_with_errors() -> str:
        """Create a Python file with various type errors."""
        return '''
"""Python file with type errors for testing."""

# Missing return type annotation
def get_name():
    return "John Doe"

# Missing parameter annotations
def calculate(x, y):
    return x + y

# Type mismatch
age: int = "twenty-five"

# Incompatible return type
def get_count() -> int:
    return "42"

# Missing annotations in method
class Calculator:
    def add(self, a, b):
        return a + b
        
# Using Any without importing
def process(data: Any) -> None:
    pass

# Optional used incorrectly
from typing import Optional

def find_user(user_id: int) -> Optional[str]:
    if user_id > 0:
        return user_id  # Returning int instead of str
    return None
'''

    @staticmethod
    def create_partial_annotations() -> str:
        """Create file with partial type annotations."""
        return '''
"""File with partial type annotations."""

from typing import List


def typed_function(x: int) -> int:
    """Fully typed function."""
    return x * 2


def partial_function(x: int, y):  # Missing annotation for y
    """Partially typed function."""
    return x + y


def untyped_function(x, y):  # No annotations
    """Untyped function."""
    return x * y


class MixedClass:
    """Class with mixed typing."""
    
    def __init__(self, name: str):  # Missing return annotation
        self.name = name
        
    def typed_method(self) -> str:
        return self.name
        
    def untyped_method(self, value):
        return value * 2
'''


class MockMypyRunner:
    """Mock MyPy runner for testing."""
    
    def __init__(self, errors: Optional[List[MypyError]] = None):
        self.errors = errors or []
        self.call_count = 0
        
    def run(self, files: List[Path], args: Optional[List[str]] = None) -> MypyResult:
        """Mock run method."""
        self.call_count += 1
        
        return MypyResult(
            success=len(self.errors) == 0,
            errors=self.errors,
            warnings=[],
            notes=[],
            files_checked=len(files),
            execution_time=0.1 * len(files),
            command=["mypy"] + (args or []) + [str(f) for f in files],
            return_code=0 if len(self.errors) == 0 else 1,
            raw_output=f"Found {len(self.errors)} errors in {len(files)} files"
        )


class CLIOutputCapture:
    """Capture and analyze CLI output."""
    
    def __init__(self):
        self.lines: List[str] = []
        self.colors_found: Dict[str, int] = {}
        
    def capture(self, text: str) -> None:
        """Capture output text."""
        self.lines.append(text)
        self._analyze_colors(text)
        
    def _analyze_colors(self, text: str) -> None:
        """Analyze ANSI color codes in text."""
        import re
        
        # Common ANSI patterns
        patterns = {
            "red": r"\033\[31m",
            "green": r"\033\[32m", 
            "yellow": r"\033\[33m",
            "blue": r"\033\[34m",
            "magenta": r"\033\[35m",
            "cyan": r"\033\[36m",
            "bold": r"\033\[1m",
            "reset": r"\033\[0m"
        }
        
        for color, pattern in patterns.items():
            matches = len(re.findall(pattern, text))
            self.colors_found[color] = self.colors_found.get(color, 0) + matches
            
    def get_text(self) -> str:
        """Get captured text."""
        return "\n".join(self.lines)
        
    def has_color(self, color: str) -> bool:
        """Check if specific color was used."""
        return self.colors_found.get(color, 0) > 0
        
    def clear(self) -> None:
        """Clear captured output."""
        self.lines.clear()
        self.colors_found.clear()


@contextmanager
def temporary_env(**kwargs):
    """Temporarily set environment variables."""
    old_env = {}
    
    for key, value in kwargs.items():
        old_env[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(value)
            
    try:
        yield
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def temporary_cwd(path: Path):
    """Temporarily change working directory."""
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def create_test_progress_file(path: Path, data: Dict[str, Any]) -> None:
    """Create a test progress file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def run_cli_command(args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run a CLI command and return result."""
    cmd = [sys.executable] + args
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    return result


def assert_mypy_error(error: MypyError, **expected):
    """Assert MyPy error has expected attributes."""
    for attr, value in expected.items():
        actual = getattr(error, attr)
        assert actual == value, f"Expected {attr}={value}, got {actual}"


def create_mock_tutorial_progress() -> Dict[str, Any]:
    """Create mock tutorial progress data."""
    return {
        "completed": ["hello_world", "type_annotations_basics"],
        "in_progress": {
            "advanced_types": {
                "current_page": 3,
                "total_pages": 10,
                "started": "2024-01-15T10:30:00"
            }
        },
        "scores": {
            "hello_world": 100,
            "type_annotations_basics": 85
        },
        "total_time_spent": 3600.5,
        "last_activity": "2024-01-15T14:30:00"
    }


def wait_for_file(path: Path, timeout: float = 5.0) -> bool:
    """Wait for a file to be created."""
    start = time.time()
    
    while time.time() - start < timeout:
        if path.exists():
            return True
        time.sleep(0.1)
        
    return False


def compare_json_files(file1: Path, file2: Path, ignore_keys: Optional[List[str]] = None) -> bool:
    """Compare two JSON files, optionally ignoring certain keys."""
    ignore_keys = ignore_keys or []
    
    with open(file1) as f1, open(file2) as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
        
    def remove_keys(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """Remove specified keys from dict recursively."""
        if not isinstance(d, dict):
            return d
            
        result = {}
        for k, v in d.items():
            if k not in keys:
                if isinstance(v, dict):
                    result[k] = remove_keys(v, keys)
                elif isinstance(v, list):
                    result[k] = [remove_keys(item, keys) if isinstance(item, dict) else item for item in v]
                else:
                    result[k] = v
        return result
        
    if ignore_keys:
        data1 = remove_keys(data1, ignore_keys)
        data2 = remove_keys(data2, ignore_keys)
        
    return data1 == data2


class ProgressDataBuilder:
    """Build test progress data."""
    
    @staticmethod
    def create_empty() -> Dict[str, Any]:
        """Create empty progress data."""
        return {
            "total_errors_found": 0,
            "total_errors_fixed": 0,
            "total_files_checked": 0,
            "total_sessions": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "last_session": None,
            "daily_stats": {},
            "achievements_unlocked": [],
            "achievements_available": [],
            "tutorial_progress": {
                "completed": [],
                "in_progress": {},
                "scores": {},
                "total_time_spent": 0.0,
                "last_activity": None
            }
        }
        
    @staticmethod
    def create_with_progress() -> Dict[str, Any]:
        """Create progress data with some progress."""
        return {
            "total_errors_found": 42,
            "total_errors_fixed": 35,
            "total_files_checked": 15,
            "total_sessions": 5,
            "current_streak": 3,
            "longest_streak": 5,
            "last_session": "2024-01-15T14:30:00",
            "daily_stats": {
                "2024-01-15": {
                    "sessions_count": 2,
                    "total_files_checked": 8,
                    "total_errors_found": 12,
                    "total_errors_fixed": 10,
                    "total_time_spent": 1800.5,
                    "unique_error_types": {
                        "no-untyped-def": 5,
                        "return-value": 3,
                        "assignment": 2
                    }
                }
            },
            "achievements_unlocked": ["first_error_fixed", "ten_errors_fixed"],
            "achievements_available": ["first_error_fixed", "ten_errors_fixed", "perfect_file"],
            "tutorial_progress": {
                "completed": ["hello_world"],
                "in_progress": {},
                "scores": {"hello_world": 100},
                "total_time_spent": 600.0,
                "last_activity": "2024-01-15T10:00:00"
            }
        }