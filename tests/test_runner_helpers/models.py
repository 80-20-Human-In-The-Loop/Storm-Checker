"""
Data Models for Test Runner
============================
Data classes and types used throughout the test runner components.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class TestResult:
    """Holds test execution results."""
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total: int = 0
    not_run: int = 0
    elapsed_time: float = 0.0
    
    def update_total(self):
        """Update total based on individual counts."""
        self.total = self.passed + self.failed + self.skipped + self.errors
        
    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0 and self.errors == 0
        
    @property
    def has_issues(self) -> bool:
        """Check if there were any test issues."""
        return self.failed > 0 or self.errors > 0 or self.not_run > 0


@dataclass
class TestFailure:
    """Information about a failed test."""
    path: str  # Full test path like tests/file.py::TestClass::test_method
    error: str  # Error message
    file: Optional[str] = None  # Just the file path
    test_name: Optional[str] = None  # Just the test name
    
    def __post_init__(self):
        """Parse the path to extract file and test name."""
        if "::" in self.path:
            parts = self.path.split("::")
            self.file = parts[0]
            self.test_name = "::".join(parts[1:]) if len(parts) > 1 else None


@dataclass
class SlowTest:
    """Information about a slow test."""
    file: str
    duration: float
    test_name: Optional[str] = None
    
    @property
    def display_duration(self) -> str:
        """Format duration for display."""
        return f"{self.duration:.2f}s"


@dataclass
class CoverageInfo:
    """Coverage information for a file."""
    filepath: str
    statements: int
    missed: int
    coverage_percent: float
    missing_lines: List[int] = field(default_factory=list)
    
    @property
    def covered(self) -> int:
        """Number of covered statements."""
        return self.statements - self.missed


@dataclass
class TestRunState:
    """Complete state of a test run."""
    results: TestResult = field(default_factory=TestResult)
    failures: List[TestFailure] = field(default_factory=list)
    slow_tests: List[SlowTest] = field(default_factory=list)
    coverage_data: Dict[str, CoverageInfo] = field(default_factory=dict)
    output: str = ""
    returncode: int = 0
    stdin_blocked_files: List[str] = field(default_factory=list)
    
    # Execution metadata
    command: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return self.results.elapsed_time
        
    @property
    def has_coverage(self) -> bool:
        """Check if coverage data is available."""
        return bool(self.coverage_data)


@dataclass
class DiagnosticIssue:
    """A single diagnostic issue found."""
    category: str  # e.g., "import", "naming", "stdin", "timeout"
    severity: str  # "error", "warning", "info"
    message: str
    files: List[str] = field(default_factory=list)
    suggestion: Optional[str] = None


@dataclass
class DiagnosticReport:
    """Complete diagnostic report."""
    issues: List[DiagnosticIssue] = field(default_factory=list)
    test_files_found: int = 0
    test_count_estimate: int = 0
    config_files: List[str] = field(default_factory=list)
    pytest_plugins: List[str] = field(default_factory=list)
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(issue.severity == "error" for issue in self.issues)
        
    @property
    def issue_count(self) -> Dict[str, int]:
        """Count issues by severity."""
        counts = {"error": 0, "warning": 0, "info": 0}
        for issue in self.issues:
            counts[issue.severity] = counts.get(issue.severity, 0) + 1
        return counts


@dataclass
class TestFile:
    """Information about a test file."""
    path: Path
    test_count: int = 0
    has_slow_marker: bool = False
    has_stdin_usage: bool = False
    import_error: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if this is a valid test file."""
        return self.path.name.startswith("test_") and self.import_error is None
        
    @property
    def relative_path(self) -> str:
        """Get relative path from tests directory."""
        try:
            return str(self.path.relative_to(Path("tests")))
        except ValueError:
            return str(self.path)


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    command: List[str]
    start_time: float
    timeout: float
    memory_limit_mb: int
    current_file: Optional[str] = None
    killed: bool = False
    kill_reason: Optional[str] = None