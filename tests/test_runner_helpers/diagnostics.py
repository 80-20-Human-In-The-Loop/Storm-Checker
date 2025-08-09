"""
Diagnostics for Test Runner
============================
Provides diagnostic capabilities to identify test suite issues.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import List, Optional

from .models import DiagnosticReport, DiagnosticIssue, TestFile
from .executor import TestExecutor


class Diagnostics:
    """Provides diagnostic capabilities for the test suite."""
    
    def __init__(self, args):
        self.args = args
        self.executor = TestExecutor(args)
        self.test_dir = Path(__file__).parent.parent
        
    def run(self) -> int:
        """Run full diagnostics and print report."""
        report = self.run_full_diagnostics()
        self.print_report(report)
        return 0 if not report.has_critical_issues else 1
        
    def run_full_diagnostics(self) -> DiagnosticReport:
        """Run comprehensive diagnostic checks."""
        report = DiagnosticReport()
        
        # Check test discovery
        test_files = self.check_test_discovery(report)
        
        # Check imports
        self.check_imports(test_files[:10], report)
        
        # Check for common issues
        self.check_common_issues(test_files[:20], report)
        
        # Check pytest configuration
        self.check_pytest_config(report)
        
        # Check fixtures
        self.check_fixtures(report)
        
        # Estimate test count
        self.estimate_test_count(report)
        
        return report
        
    def check_test_discovery(self, report: DiagnosticReport) -> List[str]:
        """Check test file discovery."""
        test_files = self.executor.discover_test_files()
        report.test_files_found = len(test_files)
        
        if not test_files:
            report.issues.append(DiagnosticIssue(
                category="discovery",
                severity="error",
                message="No test files found!",
                suggestion="Ensure test files are in tests/ directory and start with 'test_'"
            ))
        else:
            # Check for naming issues
            bad_names = [f for f in test_files if not os.path.basename(f).startswith("test_")]
            if bad_names:
                report.issues.append(DiagnosticIssue(
                    category="naming",
                    severity="warning",
                    message=f"Found {len(bad_names)} test files not starting with 'test_'",
                    files=bad_names[:5],
                    suggestion="Rename files to start with 'test_' for pytest discovery"
                ))
                
        return test_files
        
    def check_imports(self, test_files: List[str], report: DiagnosticReport):
        """Check for import errors in test files."""
        import_errors = []
        
        for test_file in test_files:
            try:
                spec = importlib.util.spec_from_file_location("test_module", test_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            except Exception as e:
                import_errors.append((test_file, str(e)))
                
        if import_errors:
            report.issues.append(DiagnosticIssue(
                category="import",
                severity="error",
                message=f"Found {len(import_errors)} import errors",
                files=[f for f, _ in import_errors],
                suggestion="Fix import paths and missing dependencies"
            ))
            
    def check_common_issues(self, test_files: List[str], report: DiagnosticReport):
        """Check for common test issues."""
        stdin_tests = []
        slow_markers = []
        
        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                    
                    # Check for stdin usage
                    if 'input(' in content or 'sys.stdin' in content:
                        stdin_tests.append(test_file)
                        
                    # Check for slow markers
                    if '@pytest.mark.slow' in content or '@slow' in content:
                        slow_markers.append(test_file)
            except:
                pass
                
        if stdin_tests:
            report.issues.append(DiagnosticIssue(
                category="stdin",
                severity="warning",
                message=f"Found {len(stdin_tests)} tests that may block on stdin",
                files=stdin_tests[:3],
                suggestion="Mock input() or sys.stdin in these tests"
            ))
            
        if slow_markers:
            report.issues.append(DiagnosticIssue(
                category="performance",
                severity="info",
                message=f"Found {len(slow_markers)} files with slow test markers",
                files=slow_markers[:3],
                suggestion="Use -m 'not slow' to skip slow tests"
            ))
            
    def check_pytest_config(self, report: DiagnosticReport):
        """Check for pytest configuration files."""
        config_files = ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                report.config_files.append(config_file)
                
                # Check configuration content
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if "timeout" in content:
                            report.issues.append(DiagnosticIssue(
                                category="config",
                                severity="info",
                                message=f"Timeout configuration detected in {config_file}"
                            ))
                except:
                    pass
                    
        if not report.config_files:
            report.issues.append(DiagnosticIssue(
                category="config",
                severity="info",
                message="No pytest configuration file found",
                suggestion="Consider adding pyproject.toml or pytest.ini for test configuration"
            ))
            
    def check_fixtures(self, report: DiagnosticReport):
        """Check pytest fixtures availability."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--fixtures", "-q"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                # Count fixtures
                fixture_count = result.stdout.count("@pytest.fixture")
                if fixture_count > 0:
                    report.issues.append(DiagnosticIssue(
                        category="fixtures",
                        severity="info",
                        message=f"Found {fixture_count} fixtures available"
                    ))
        except subprocess.TimeoutExpired:
            report.issues.append(DiagnosticIssue(
                category="fixtures",
                severity="error",
                message="Fixture collection timed out",
                suggestion="Check for import loops or circular dependencies"
            ))
        except Exception as e:
            report.issues.append(DiagnosticIssue(
                category="fixtures",
                severity="warning",
                message=f"Could not check fixtures: {e}"
            ))
            
    def estimate_test_count(self, report: DiagnosticReport):
        """Estimate total test count."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                # Look for test count
                for line in result.stdout.strip().split('\n'):
                    if 'test' in line.lower() and 'collected' in line.lower():
                        import re
                        match = re.search(r'(\d+)\s+test', line)
                        if match:
                            report.test_count_estimate = int(match.group(1))
                            break
        except:
            pass
            
    def print_report(self, report: DiagnosticReport):
        """Print diagnostic report."""
        from storm_checker.cli.colors import print_header, print_success, print_error, print_warning, print_info
        
        print_header("Running Test Suite Diagnostics")
        print("=" * 80)
        
        # Test discovery
        print(f"\n🔍 Test Discovery:")
        if report.test_files_found > 0:
            print_success(f"  ✅ Found {report.test_files_found} test files")
        else:
            print_error("  ❌ No test files found!")
            
        # Configuration
        if report.config_files:
            print(f"\n⚙️  Configuration:")
            for config in report.config_files:
                print_success(f"  ✅ Found {config}")
        else:
            print_warning("\n⚠️  No pytest configuration found")
            
        # Test count
        if report.test_count_estimate > 0:
            print(f"\n📊 Test Count:")
            print_info(f"  ℹ️  Approximately {report.test_count_estimate} tests")
            
        # Issues
        if report.issues:
            counts = report.issue_count
            print(f"\n🐛 Issues Found:")
            
            # Group by severity
            errors = [i for i in report.issues if i.severity == "error"]
            warnings = [i for i in report.issues if i.severity == "warning"]
            infos = [i for i in report.issues if i.severity == "info"]
            
            if errors:
                print_error(f"  ❌ {len(errors)} Errors:")
                for issue in errors[:3]:
                    print(f"      • {issue.message}")
                    if issue.suggestion:
                        print(f"        💡 {issue.suggestion}")
                        
            if warnings:
                print_warning(f"  ⚠️  {len(warnings)} Warnings:")
                for issue in warnings[:3]:
                    print(f"      • {issue.message}")
                    if issue.suggestion:
                        print(f"        💡 {issue.suggestion}")
                        
            if infos:
                print_info(f"  ℹ️  {len(infos)} Suggestions:")
                for issue in infos[:3]:
                    print(f"      • {issue.message}")
                    
        # Summary
        print("\n" + "=" * 80)
        print_header("Diagnostic Summary")
        
        if not report.has_critical_issues:
            print_success("✅ No critical issues found!")
            print_info("\nRecommendations:")
            print("  • Use --quick mode for faster test runs")
            print("  • Use --debug-runner for detailed debugging")
            print("  • Add pytest-timeout to prevent hanging tests")
        else:
            print_error(f"❌ Found critical issues that need attention")
            print_info("\nTry running:")
            print("  • ./tests/run_tests.py --quick  # For faster execution")
            print("  • ./tests/run_tests.py --debug-runner  # For detailed debugging")
            
        print("=" * 80)