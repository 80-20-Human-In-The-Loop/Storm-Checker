"""
Pytest Configuration and Fixtures
=================================
Shared fixtures and configuration for Storm Checker tests.
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storm_checker.logic.mypy_runner import MypyError, MypyResult
from storm_checker.models.progress_models import (
    Achievement, AchievementCategory, SessionStats, 
    DailyStats, TutorialProgress, ProgressData
)


# Test markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast)")
    config.addinivalue_line("markers", "integration: Integration tests (slower)")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "cli: CLI interface tests")
    config.addinivalue_line("markers", "mypy: Tests requiring MyPy")


# Fixtures for temporary directories
@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def temp_project(temp_dir):
    """Create a temporary Python project structure."""
    # Create basic project structure
    (temp_dir / "src").mkdir()
    (temp_dir / "tests").mkdir()
    (temp_dir / "src" / "__init__.py").touch()
    
    # Create sample Python files
    (temp_dir / "src" / "main.py").write_text("""
def greet(name: str) -> str:
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    return a + b
""")
    
    (temp_dir / "src" / "utils.py").write_text("""
from typing import List, Optional

def process_items(items: List[str]) -> List[str]:
    return [item.upper() for item in items]

def find_item(items: List[str], target: str) -> Optional[int]:
    try:
        return items.index(target)
    except ValueError:
        return None
""")
    
    # Create file with type errors
    (temp_dir / "src" / "errors.py").write_text("""
def bad_function(x):  # Missing type annotations
    return x + 1

def another_bad() -> str:
    return 42  # Type error: returning int instead of str

result = bad_function("not a number")  # Runtime error
""")
    
    yield temp_dir


# Mock MyPy fixtures
@pytest.fixture
def mock_mypy_errors():
    """Create mock MyPy errors for testing."""
    return [
        MypyError(
            file_path="src/main.py",
            line_number=5,
            column=10,
            severity="error",
            error_code="no-untyped-def",
            message="Function is missing a type annotation",
            raw_line="src/main.py:5:10: error: Function is missing a type annotation  [no-untyped-def]"
        ),
        MypyError(
            file_path="src/utils.py",
            line_number=12,
            column=4,
            severity="error",
            error_code="return-value",
            message='Incompatible return value type (got "int", expected "str")',
            raw_line='src/utils.py:12:4: error: Incompatible return value type (got "int", expected "str")  [return-value]'
        ),
        MypyError(
            file_path="src/main.py",
            line_number=8,
            column=None,
            severity="warning",
            error_code="unused-ignore",
            message="Unused 'type: ignore' comment",
            raw_line="src/main.py:8: warning: Unused 'type: ignore' comment"
        )
    ]


@pytest.fixture
def mock_mypy_result(mock_mypy_errors):
    """Create a mock MyPy result."""
    return MypyResult(
        success=False,
        errors=[e for e in mock_mypy_errors if e.severity == "error"],
        warnings=[e for e in mock_mypy_errors if e.severity == "warning"],
        notes=[],
        files_checked=3,
        execution_time=1.234,
        command=["mypy", "src/"],
        return_code=1,
        raw_output="Found 2 errors in 2 files (checked 3 source files)"
    )


# Progress tracking fixtures
@pytest.fixture
def sample_session_stats():
    """Create sample session statistics."""
    return SessionStats(
        timestamp=datetime.now(),
        files_checked=10,
        errors_found=5,
        errors_fixed=3,
        time_spent=120.5,
        error_types={
            "no-untyped-def": 3,
            "return-value": 2
        },
        files_modified=["src/main.py", "src/utils.py"]
    )


@pytest.fixture
def sample_achievements():
    """Create sample achievements."""
    return [
        Achievement(
            id="first_error_fixed",
            name="First Steps",
            description="Fix your first type error",
            category=AchievementCategory.BEGINNER,
            icon="🎯",
            points=10,
            requirement={"errors_fixed": 1}
        ),
        Achievement(
            id="ten_errors_fixed",
            name="Error Hunter",
            description="Fix 10 type errors",
            category=AchievementCategory.PROGRESS,
            icon="🏹",
            points=50,
            requirement={"errors_fixed": 10}
        ),
        Achievement(
            id="perfect_file",
            name="Perfectionist",
            description="Make a file 100% type safe",
            category=AchievementCategory.MASTERY,
            icon="✨",
            points=100,
            requirement={"perfect_files": 1}
        )
    ]


@pytest.fixture
def sample_progress_data(sample_achievements):
    """Create sample progress data."""
    return ProgressData(
        total_errors_found=150,
        total_errors_fixed=89,
        total_files_checked=45,
        total_sessions=12,
        current_streak=3,
        longest_streak=7,
        last_session=datetime.now(),
        daily_stats={},
        achievements_unlocked=["first_error_fixed"],
        achievements_available=[a.id for a in sample_achievements],
        tutorial_progress=TutorialProgress(
            completed=["hello_world"],
            scores={"hello_world": 100}
        )
    )


# Configuration fixtures
@pytest.fixture
def test_config():
    """Create test configuration."""
    return {
        "mypy_args": ["--show-error-codes", "--strict"],
        "educational_mode": True,
        "show_achievements": True,
        "track_progress": True,
        "progress_file": ".test_progress.json"
    }


# CLI output capture
@pytest.fixture
def capture_cli_output(monkeypatch):
    """Capture CLI output for testing."""
    output = []
    
    def mock_print(*args, **kwargs):
        output.append(" ".join(str(arg) for arg in args))
    
    monkeypatch.setattr("builtins.print", mock_print)
    return output


# Mock file system
@pytest.fixture
def mock_fs(tmp_path):
    """Create a mock file system for testing."""
    class MockFS:
        def __init__(self, base_path):
            self.base = base_path
            
        def create_file(self, path: str, content: str = "") -> Path:
            """Create a file with content."""
            file_path = self.base / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return file_path
            
        def create_python_module(self, name: str, with_errors: bool = False) -> Path:
            """Create a Python module."""
            if with_errors:
                content = """
def bad_function(x):  # No type annotation
    return x + 1

value: str = 123  # Type error
"""
            else:
                content = """
from typing import List, Optional

def good_function(x: int) -> int:
    return x + 1

def process(items: List[str]) -> Optional[str]:
    return items[0] if items else None
"""
            return self.create_file(f"{name}.py", content)
            
    return MockFS(tmp_path)


# Test data generators
@pytest.fixture
def error_generator():
    """Generate various types of MyPy errors for testing."""
    def generate(error_type: str, count: int = 1) -> List[MypyError]:
        errors = []
        
        templates = {
            "no-untyped-def": {
                "message": "Function is missing a type annotation",
                "severity": "error"
            },
            "return-value": {
                "message": 'Incompatible return value type (got "{}", expected "{}")',
                "severity": "error"
            },
            "assignment": {
                "message": 'Incompatible types in assignment (expression has type "{}", variable has type "{}")',
                "severity": "error"
            },
            "unused-ignore": {
                "message": "Unused 'type: ignore' comment",
                "severity": "warning"
            }
        }
        
        template = templates.get(error_type, templates["no-untyped-def"])
        
        for i in range(count):
            error = MypyError(
                file_path=f"test_file_{i}.py",
                line_number=10 + i,
                column=5,
                severity=template["severity"],
                error_code=error_type,
                message=template["message"].format("int", "str"),
                raw_line=f"test_file_{i}.py:{10+i}:5: {template['severity']}: {template['message']}"
            )
            errors.append(error)
            
        return errors
        
    return generate


# Async test support
@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Performance testing
@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer for performance tests."""
    import time
    
    class Timer:
        def __init__(self):
            self.times = {}
            
        def start(self, name: str):
            self.times[name] = time.time()
            
        def stop(self, name: str) -> float:
            if name not in self.times:
                raise ValueError(f"Timer '{name}' not started")
            elapsed = time.time() - self.times[name]
            del self.times[name]
            return elapsed
            
    return Timer()


# Skip conditions
skip_if_no_mypy = pytest.mark.skipif(
    shutil.which("mypy") is None,
    reason="MyPy not installed"
)

skip_if_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Test not compatible with Windows"
)

skip_if_slow = pytest.mark.skipif(
    "--skip-slow" in sys.argv,
    reason="Skipping slow tests"
)