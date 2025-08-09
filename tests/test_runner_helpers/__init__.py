"""
Test Runner Helper Components
==============================
Modular components for the Storm Checker test runner.
"""

# Models
from .models import (
    TestResult,
    TestFailure,
    SlowTest,
    TestRunState,
    DiagnosticReport,
    DiagnosticIssue,
    CoverageInfo,
    TestFile,
    ProcessInfo
)

# Core components
from .parser import ResultParser
from .monitor import ProcessMonitor

# Note: These imports are conditional to avoid circular dependencies
# They should be imported where needed
__all__ = [
    # Models
    'TestResult',
    'TestFailure', 
    'SlowTest',
    'TestRunState',
    'DiagnosticReport',
    'DiagnosticIssue',
    'CoverageInfo',
    'TestFile',
    'ProcessInfo',
    
    # Core Components (others imported as needed to avoid circular deps)
    'ResultParser',
    'ProcessMonitor',
]