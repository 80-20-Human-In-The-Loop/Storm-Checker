"""
Known Issues Registry for Test Runner
======================================
Registry of known problematic tests that need special handling.
"""

from typing import List, Dict, Any


# Tests that hang indefinitely and must be excluded
HANGING_TESTS: List[str] = [
    # This test hangs because mock_rich_unavailable doesn't properly mock input()
    "tests/cli/components/test_rich_terminal.py::TestRichTerminal::test_prompt_without_rich",
    "tests/cli/components/test_rich_terminal.py::TestRichTerminal::test_prompt_without_rich_empty_response",
    "tests/cli/components/test_rich_terminal.py::TestRichTerminal::test_prompt_without_rich_no_default",
    "tests/cli/components/test_rich_terminal.py::TestRichTerminal::test_confirm_without_rich",
    "tests/cli/components/test_rich_terminal.py::TestRichTerminal::test_confirm_without_rich_no_response",
    "tests/cli/components/test_rich_terminal.py::TestRichTerminal::test_confirm_without_rich_negative",
]

# Tests that are flaky and may fail intermittently
FLAKY_TESTS: List[str] = []

# Tests that take longer than 5 seconds
SLOW_TESTS: List[str] = []

# Tests that should be run in isolation due to side effects
ISOLATION_REQUIRED: List[str] = []


def get_exclusion_args() -> List[str]:
    """Get pytest arguments to exclude known hanging tests."""
    if not HANGING_TESTS:
        return []
    
    # Build pytest deselect arguments
    args = []
    for test in HANGING_TESTS:
        args.extend(["--deselect", test])
    
    return args


def should_exclude_test(test_path: str) -> bool:
    """Check if a test should be excluded."""
    # Check if test matches any hanging test pattern
    for hanging_test in HANGING_TESTS:
        if hanging_test in test_path or test_path in hanging_test:
            return True
    return False


def get_hanging_test_info() -> Dict[str, Any]:
    """Get information about hanging tests."""
    return {
        "count": len(HANGING_TESTS),
        "tests": HANGING_TESTS,
        "message": f"Excluding {len(HANGING_TESTS)} known hanging tests",
        "hint": "Use --include-hanging to run these tests (may hang!)"
    }