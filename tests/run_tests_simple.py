#!/usr/bin/env python3
"""Simple test runner to diagnose hanging issue."""

import subprocess
import sys

# Run pytest with minimal options
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--no-header"],
    text=True
)

sys.exit(result.returncode)