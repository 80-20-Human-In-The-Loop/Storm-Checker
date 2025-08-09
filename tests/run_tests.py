#!/usr/bin/env python3
"""
Storm Checker Test Runner
=========================
Beautiful test runner using modular components for better maintainability.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for storm_checker imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our modular components
from test_runner_helpers.executor import TestExecutor
from test_runner_helpers.reporter import Reporter
from test_runner_helpers.diagnostics import Diagnostics
from test_runner_helpers.coverage import CoverageAnalyzer
from test_runner_helpers.hang_detector import HangDetector

# Import Storm Checker CLI utilities
try:
    from storm_checker.cli.colors import ColorPrinter, BOLD, RESET
except ImportError as e:
    print(f"Failed to import storm_checker modules: {e}")
    print("Please ensure storm_checker is properly installed.")
    sys.exit(1)


class TestRunner:
    """Orchestrates test execution using modular components."""
    
    def __init__(self, args: argparse.Namespace):
        """Initialize the test runner with components."""
        self.args = args
        self.reporter = Reporter(args)
        self.executor = TestExecutor(args, self.reporter)
        self.diagnostics = Diagnostics(args) if args.diagnose else None
        self.coverage = CoverageAnalyzer(args) if args.coverage else None
        
    def run(self) -> int:
        """Run tests based on selected mode."""
        # Diagnostic mode - analyze test suite health
        if self.args.diagnose:
            return self.diagnostics.run()
            
        # Hang detection mode - find hanging tests
        if self.args.find_hanging:
            detector = HangDetector(
                timeout=self.args.test_timeout,
                verbose=self.args.verbose
            )
            results = detector.find_hanging_tests()
            print(results["summary"])
            return 0 if not results["hanging"] else 1
            
        # Normal test execution
        if not self.args.no_color and not self.args.quiet:
            self.reporter.clear_screen()
            
        # Print header with configuration
        test_count = len(self.executor.discover_test_files(self.args.pattern))
        self.reporter.print_header(test_count)
        
        # Auto-enable quick mode for full suite with coverage
        if self.args.coverage and not self.args.pattern and not self.args.quick and not self.args.no_quick:
            print("💡 Auto-enabling quick mode for full suite with coverage")
            print("   (Use --no-quick to override)")
            self.args.quick = True
        
        # Execute tests
        state = self.executor.run_tests()
        
        # Print results based on display mode
        self.reporter.print_results(state)
        
        return state.returncode


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Storm Checker Test Runner - Beautiful test execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{BOLD}Examples:{RESET}
  {ColorPrinter.primary('python tests/run_tests.py')}                    # Run all tests
  {ColorPrinter.primary('python tests/run_tests.py -v')}                 # Verbose output
  {ColorPrinter.primary('python tests/run_tests.py -c')}                 # With coverage
  {ColorPrinter.primary('python tests/run_tests.py -p test_colors')}     # Run specific tests
  {ColorPrinter.primary('python tests/run_tests.py -m unit')}            # Run unit tests only
  {ColorPrinter.primary('python tests/run_tests.py --dashboard')}        # Dashboard view
  {ColorPrinter.primary('python tests/run_tests.py --diagnose')}         # Run diagnostics
  {ColorPrinter.primary('python tests/run_tests.py --quick')}            # Quick mode
        """
    )
    
    # Output options
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    output_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Minimal output"
    )
    
    # Test selection
    parser.add_argument(
        "-p", "--pattern",
        help="Run tests matching pattern"
    )
    parser.add_argument(
        "-m", "--mark",
        help="Run tests with specific marker (unit, integration, slow)"
    )
    
    # Features
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--failed-first",
        action="store_true",
        help="Run previously failed tests first"
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Show results in dashboard format"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--slow-test-threshold",
        type=float,
        default=1.0,
        help="Threshold in seconds for slow test detection (default: 1.0s)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output for troubleshooting"
    )
    parser.add_argument(
        "--maxfail",
        type=int,
        help="Stop after N failures (useful for quick testing)"
    )
    
    # Enhanced options for debugging
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: Run all tests in one batch (faster, no per-file progress)"
    )
    parser.add_argument(
        "--debug-runner",
        action="store_true",
        help="Show detailed test runner diagnostics (which test is running, memory usage, etc.)"
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Run diagnostic checks on test suite (find slow tests, hanging tests, etc.)"
    )
    parser.add_argument(
        "--per-test-timeout",
        type=int,
        default=10,
        help="Timeout per individual test in seconds (default: 10s, use 0 to disable)"
    )
    
    # Safety features
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout per test file in seconds (default: 30s)"
    )
    parser.add_argument(
        "--max-memory",
        type=int,
        default=2048,
        help="Maximum memory usage in MB (default: 2048MB / 2GB)"
    )
    parser.add_argument(
        "--safety-off",
        action="store_true",
        help="Disable all safety features (timeout and memory limits)"
    )
    parser.add_argument(
        "--no-coverage-collection",
        action="store_true",
        help="Skip separate coverage collection pass (use with caution)"
    )
    parser.add_argument(
        "--no-quick",
        action="store_true",
        help="Disable auto-quick mode for coverage runs"
    )
    parser.add_argument(
        "--include-hanging",
        action="store_true",
        help="Include known hanging tests (WARNING: may hang indefinitely!)"
    )
    
    # Diagnostic options
    parser.add_argument(
        "--find-hanging",
        action="store_true",
        help="Scan for hanging tests by running each test with timeout"
    )
    parser.add_argument(
        "--test-timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for --find-hanging mode (default: 5.0s)"
    )
    
    # Coverage insights options
    parser.add_argument(
        "--no-insights",
        action="store_true",
        help="Disable actionable coverage insights"
    )
    parser.add_argument(
        "--export-insights",
        type=str,
        metavar="FILE",
        help="Export coverage insights to JSON file"
    )
    
    return parser


def main() -> int:
    """Main entry point for the test runner."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create and run the test runner
    runner = TestRunner(args)
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())