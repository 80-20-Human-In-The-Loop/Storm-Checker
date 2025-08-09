"""
Pytest configuration for scripts tests.
Ensures clean test isolation and prevents import pollution.
"""

import pytest
import sys
from typing import Set


@pytest.fixture(autouse=True)
def clean_imports():
    """Ensure clean import state for each test."""
    # Capture current modules before test
    before = set(sys.modules.keys())
    original_argv = sys.argv.copy()
    
    yield
    
    # Restore sys.argv
    sys.argv = original_argv
    
    # Clean up any new storm_checker imports after test
    after = set(sys.modules.keys())
    new_modules = after - before
    
    for mod in new_modules:
        if 'storm_checker.scripts' in mod or 'scripts.' in mod:
            sys.modules.pop(mod, None)


@pytest.fixture
def isolated_import():
    """Fixture for tests that need completely isolated imports."""
    # Save all storm_checker modules
    saved_modules = {}
    for mod in list(sys.modules.keys()):
        if 'storm_checker' in mod or mod in ['scripts', 'tutorial', 'progress', 'check_mypy']:
            saved_modules[mod] = sys.modules.get(mod)
            sys.modules.pop(mod, None)
    
    yield
    
    # Restore saved modules
    for mod, saved in saved_modules.items():
        if saved:
            sys.modules[mod] = saved