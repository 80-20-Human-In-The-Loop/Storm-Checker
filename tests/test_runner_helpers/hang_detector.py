"""
Hang Detector for Test Runner
==============================
Detects and reports hanging tests by running them in isolation.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .known_issues import HANGING_TESTS


@dataclass
class TestExecutionResult:
    """Result of executing a single test."""
    test_path: str
    duration: float
    status: str  # "passed", "failed", "skipped", "timeout", "error"
    output: str = ""
    error: str = ""


class HangDetector:
    """Detects hanging tests by running them individually with timeouts."""
    
    def __init__(self, timeout: float = 5.0, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose
        self.test_dir = Path(__file__).parent.parent
        
    def find_hanging_tests(self, test_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find all hanging tests in the test suite."""
        if test_files is None:
            test_files = self._discover_test_files()
            
        print(f"🔍 Scanning {len(test_files)} test files for hanging tests...")
        print(f"   Using {self.timeout}s timeout per test")
        
        hanging_tests = []
        slow_tests = []
        passed_tests = []
        failed_tests = []
        
        for i, test_file in enumerate(test_files, 1):
            if self.verbose:
                print(f"\n[{i}/{len(test_files)}] Testing: {test_file}")
            else:
                print(f".", end="", flush=True)
                
            result = self._run_test_with_timeout(test_file)
            
            if result.status == "timeout":
                hanging_tests.append(result)
                print(f"\n❌ HANG DETECTED: {test_file} (>{self.timeout}s)")
            elif result.duration > self.timeout / 2:
                slow_tests.append(result)
                if self.verbose:
                    print(f"   ⚠️  Slow: {result.duration:.2f}s")
            elif result.status == "failed":
                failed_tests.append(result)
            else:
                passed_tests.append(result)
                
        if not self.verbose:
            print()  # New line after dots
            
        return {
            "hanging": hanging_tests,
            "slow": slow_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "summary": self._generate_summary(hanging_tests, slow_tests, passed_tests, failed_tests)
        }
        
    def test_single_file(self, test_file: str) -> TestExecutionResult:
        """Test a single file for hanging."""
        print(f"Testing: {test_file}")
        result = self._run_test_with_timeout(test_file)
        
        if result.status == "timeout":
            print(f"❌ Test hung after {self.timeout}s")
            print("   This test needs to be added to HANGING_TESTS in known_issues.py")
        else:
            print(f"✅ Test completed in {result.duration:.2f}s")
            
        return result
        
    def _run_test_with_timeout(self, test_file: str) -> TestExecutionResult:
        """Run a single test file with timeout."""
        start_time = time.time()
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_file,
            "-xvs",  # Stop on first failure, verbose, no capture
            "--tb=short"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            # Determine status from return code
            if result.returncode == 0:
                status = "passed"
            elif result.returncode == 1:
                status = "failed"
            elif result.returncode == 5:
                status = "skipped"
            else:
                status = "error"
                
            return TestExecutionResult(
                test_path=test_file,
                duration=duration,
                status=status,
                output=result.stdout,
                error=result.stderr
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestExecutionResult(
                test_path=test_file,
                duration=duration,
                status="timeout",
                error=f"Test exceeded {self.timeout}s timeout"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestExecutionResult(
                test_path=test_file,
                duration=duration,
                status="error",
                error=str(e)
            )
            
    def _discover_test_files(self) -> List[str]:
        """Discover all test files."""
        test_files = []
        
        for root, dirs, files in os.walk(self.test_dir):
            # Skip __pycache__ and other non-test directories
            dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.')]
            
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(os.path.join(root, file))
                    
        return sorted(test_files)
        
    def _generate_summary(self, hanging: List, slow: List, passed: List, failed: List) -> str:
        """Generate a summary report."""
        total = len(hanging) + len(slow) + len(passed) + len(failed)
        
        lines = [
            "\n" + "=" * 60,
            "HANG DETECTION SUMMARY",
            "=" * 60,
            f"Total tests scanned: {total}",
            f"✅ Passed: {len(passed)}",
            f"❌ Failed: {len(failed)}",
            f"⚠️  Slow (>{self.timeout/2}s): {len(slow)}",
            f"🔴 Hanging (>{self.timeout}s): {len(hanging)}",
        ]
        
        if hanging:
            lines.append("\nHANGING TESTS:")
            for result in hanging:
                lines.append(f"  - {result.test_path}")
            lines.append("\nAdd these to HANGING_TESTS in known_issues.py")
            
        if slow:
            lines.append("\nSLOW TESTS:")
            for result in sorted(slow, key=lambda x: x.duration, reverse=True)[:5]:
                lines.append(f"  - {result.test_path}: {result.duration:.2f}s")
                
        # Check if any hanging tests are not in the known list
        unknown_hanging = []
        for result in hanging:
            if not any(known in result.test_path for known in HANGING_TESTS):
                unknown_hanging.append(result.test_path)
                
        if unknown_hanging:
            lines.append("\n⚠️  NEW HANGING TESTS DETECTED:")
            for test in unknown_hanging:
                lines.append(f"  - {test}")
            lines.append("\nThese should be added to known_issues.py")
            
        lines.append("=" * 60)
        
        return "\n".join(lines)