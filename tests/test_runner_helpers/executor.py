"""
Test Executor for Test Runner
==============================
Handles the actual execution of pytest and collection of results.
"""

import os
import sys
import subprocess
import time
import select
from pathlib import Path
from typing import List, Tuple, Optional
from rich.progress import Progress

from .models import TestRunState, TestResult, TestFile
from .parser import ResultParser
from .monitor import ProcessMonitor
from .reporter import Reporter
from .known_issues import get_exclusion_args, get_hanging_test_info


class TestExecutor:
    """Executes tests and collects results."""
    
    def __init__(self, args, reporter: Optional[Reporter] = None):
        self.args = args
        self.parser = ResultParser()
        self.monitor = ProcessMonitor(args)
        self.reporter = reporter or Reporter(args)
        self.test_dir = Path(__file__).parent.parent
        
    def discover_test_files(self, pattern: Optional[str] = None) -> List[str]:
        """Discover test files based on pattern."""
        test_files = []
        
        # Base directory for tests
        base_dir = self.test_dir
        
        # If pattern specified, filter files
        if pattern:
            pattern_lower = pattern.lower()
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        if pattern_lower in file.lower():
                            test_files.append(os.path.join(root, file))
        else:
            # Find all test files
            for root, dirs, files in os.walk(base_dir):
                # Skip __pycache__ and other non-test directories
                dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.')]
                
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        test_files.append(os.path.join(root, file))
                        
        return sorted(test_files)
        
    def build_pytest_args(self) -> List[str]:
        """Build pytest command line arguments."""
        args = []
        
        # Add test directory or pattern
        if self.args.pattern:
            args.extend(["-k", self.args.pattern])
        else:
            args.append(str(self.test_dir))
            
        # Add markers
        if self.args.mark:
            args.extend(["-m", self.args.mark])
            
        # Verbosity
        if self.args.verbose:
            args.append("-vv")
        elif not self.args.quiet:
            args.append("-v")
            
        # Coverage
        if self.args.coverage:
            args.extend([
                "--cov=storm_checker",
                "--cov-report=term-missing",
                "--cov-report=html"
            ])
            
        # Color
        if self.args.no_color:
            args.append("--color=no")
        else:
            args.append("--color=yes")
            
        # Capture settings
        args.extend(["--tb=short", "-ra"])
        
        # Timeout per test
        if self.args.per_test_timeout > 0:
            args.extend([
                f"--timeout={self.args.per_test_timeout}",
                "--timeout-method=thread"
            ])
            
        # Max failures
        if self.args.maxfail:
            args.extend(["--maxfail", str(self.args.maxfail)])
            
        # Exclude known hanging tests unless explicitly requested
        if not getattr(self.args, 'include_hanging', False):
            exclusion_args = get_exclusion_args()
            if exclusion_args:
                args.extend(exclusion_args)
                if not self.args.quiet:
                    info = get_hanging_test_info()
                    print(f"⚠️  {info['message']}")
                    print(f"   {info['hint']}")
            
        return args
        
    def run_tests(self) -> TestRunState:
        """Main entry point for running tests."""
        state = TestRunState()
        state.start_time = time.time()
        
        if self.args.quick:
            return self.run_quick_mode()
        else:
            return self.run_file_by_file()
            
    def run_quick_mode(self) -> TestRunState:
        """Run all tests in one batch (quick mode)."""
        state = TestRunState()
        state.start_time = time.time()
        
        # Build command
        cmd = [sys.executable, "-m", "pytest"] + self.build_pytest_args()
        state.command = cmd
        
        if self.args.debug_runner:
            print(f"[DEBUG] Running command: {' '.join(cmd)}")
            
        try:
            # Run tests
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start monitoring
            process_info = self.monitor.start_monitoring(
                process,
                "all tests",
                timeout=300  # 5 minute timeout for all tests
            )
            
            # Collect output
            output_lines = []
            with self.reporter.create_progress_context() as progress:
                task = progress.add_task("Running tests...", total=None)
                
                while True:
                    line = process.stdout.readline()
                    if not line:
                        if process.poll() is not None:
                            break
                        continue
                        
                    output_lines.append(line)
                    
                    # Update progress based on output
                    if ".py" in line and "::" in line:
                        file_name = line.split("::")[0].split("/")[-1]
                        progress.update(task, description=f"Testing: {file_name}")
                        
                    if self.args.verbose:
                        print(line, end='')
                        
            process.wait()
            state.end_time = time.time()
            state.output = ''.join(output_lines)
            state.returncode = process.returncode
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            
            # Check if killed
            if process_info.killed:
                state.returncode = 1
                print(f"\n❌ {process_info.kill_reason}")
                
        except KeyboardInterrupt:
            print("\n⚠️  Test run interrupted")
            process.terminate()
            state.returncode = 130
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            state.returncode = 1
            
        # Parse results
        state.results = self.parser.parse_pytest_output(state.output)
        state.failures = self.parser.extract_failed_tests(state.output)
        state.slow_tests = self.parser.extract_slow_tests(
            state.output,
            self.args.slow_test_threshold
        )
        
        # Parse coverage if enabled
        if self.args.coverage:
            state.coverage_data = self.parser.parse_coverage_output(state.output)
            
        state.results.elapsed_time = state.end_time - state.start_time
        return state
        
    def run_file_by_file(self) -> TestRunState:
        """Run tests file by file with detailed progress."""
        state = TestRunState()
        state.start_time = time.time()
        
        # Discover test files
        test_files = self.discover_test_files(self.args.pattern)
        if not test_files:
            print("No test files found!")
            state.returncode = 1
            return state
            
        print(f"Found {len(test_files)} test files")
        
        # Build base pytest args
        base_args = self.build_pytest_args()
        # Remove the test directory and coverage args since we'll handle them separately
        base_args = [arg for arg in base_args if not str(self.test_dir) in arg 
                     and not arg.startswith("--cov")]
        
        all_output = []
        
        # If coverage is enabled, initialize coverage tracking
        if self.args.coverage:
            # Initialize coverage data collection
            init_cmd = [sys.executable, "-m", "coverage", "erase"]
            subprocess.run(init_cmd, capture_output=True)
        
        with self.reporter.create_progress_context() as progress:
            task = progress.add_task(
                "Running tests...",
                total=len(test_files)
            )
            
            for i, test_file in enumerate(test_files):
                # Update progress
                file_name = os.path.basename(test_file)
                progress.update(task, description=f"Testing: {file_name}")
                
                # Run test file with coverage if enabled
                file_args = base_args.copy()
                if self.args.coverage:
                    # Use coverage run for each file
                    file_result = self._run_single_file_with_coverage(test_file, file_args)
                else:
                    file_result = self._run_single_file(test_file, file_args)
                
                # Aggregate results
                state.results.passed += file_result.results.passed
                state.results.failed += file_result.results.failed
                state.results.skipped += file_result.results.skipped
                state.results.errors += file_result.results.errors
                
                state.failures.extend(file_result.failures)
                state.slow_tests.extend(file_result.slow_tests)
                all_output.append(file_result.output)
                
                # Check for stdin blocking
                if file_result.stdin_blocked_files:
                    state.stdin_blocked_files.extend(file_result.stdin_blocked_files)
                    
                # Update progress
                progress.update(task, advance=1)
                
                # Check maxfail
                if self.args.maxfail and state.results.failed >= self.args.maxfail:
                    print(f"\nStopping after {state.results.failed} failures")
                    break
                    
        state.end_time = time.time()
        state.output = ''.join(all_output)
        state.results.update_total()
        state.results.elapsed_time = state.end_time - state.start_time
        
        # Run coverage collection if needed
        if self.args.coverage and not self.args.no_coverage_collection:
            coverage_output = self._collect_coverage()
            if coverage_output:
                parsed_coverage = self.parser.parse_coverage_output(coverage_output)
                if parsed_coverage:
                    state.coverage_data = parsed_coverage
                    if self.args.debug_runner:
                        print(f"[DEBUG] Coverage data parsed: {len(state.coverage_data)} files")
                else:
                    if self.args.debug_runner:
                        print(f"[DEBUG] Failed to parse coverage output")
                state.output += "\n" + coverage_output
            else:
                print("⚠️  Coverage collection was skipped or failed")
                print("💡 Tip: Use --quick mode for integrated coverage collection")
                
        state.returncode = 0 if state.results.success else 1
        return state
        
    def _run_single_file(self, test_file: str, base_args: List[str]) -> TestRunState:
        """Run a single test file."""
        state = TestRunState()
        
        # Build command for this file
        cmd = [sys.executable, "-m", "pytest", test_file] + base_args
        
        if self.args.debug_runner:
            print(f"\n[DEBUG] Running: {test_file}")
            
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            
            # Start monitoring
            process_info = self.monitor.start_monitoring(
                process,
                test_file,
                timeout=self.args.timeout
            )
            
            # Collect output with stdin detection
            output_lines = []
            last_output_time = time.time()
            
            while True:
                # Check for available output
                if sys.platform != 'win32':
                    ready = select.select([process.stdout], [], [], 0.1)
                    if not ready[0]:
                        if process.poll() is not None:
                            break
                        # Check for stdin blocking
                        if self.monitor.check_stdin_blocking(process, last_output_time):
                            process.terminate()
                            state.stdin_blocked_files.append(test_file)
                            break
                        continue
                        
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    continue
                    
                output_lines.append(line)
                last_output_time = time.time()
                
            process.wait()
            state.output = ''.join(output_lines)
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            
            # Check if killed
            if process_info.killed:
                print(f"\n⚠️  {process_info.kill_reason}")
                
        except Exception as e:
            if self.args.debug_runner:
                print(f"[DEBUG] Error running {test_file}: {e}")
            state.output = str(e)
            
        # Parse results for this file
        state.results = self.parser.parse_pytest_output(state.output)
        state.failures = self.parser.extract_failed_tests(state.output)
        
        return state
        
    def _run_single_file_with_coverage(self, test_file: str, base_args: List[str]) -> TestRunState:
        """Run a single test file with coverage tracking."""
        state = TestRunState()
        
        # Build command for this file using coverage run
        cmd = [
            sys.executable, "-m", "coverage", "run",
            "--append",  # Append to existing coverage data
            "--source=storm_checker",
            "-m", "pytest", test_file
        ] + base_args
        
        if self.args.debug_runner:
            print(f"\n[DEBUG] Running with coverage: {test_file}")
            
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            
            # Start monitoring
            process_info = self.monitor.start_monitoring(
                process,
                test_file,
                timeout=self.args.timeout
            )
            
            # Collect output with stdin detection
            output_lines = []
            last_output_time = time.time()
            
            while True:
                # Check for available output
                if sys.platform != 'win32':
                    ready = select.select([process.stdout], [], [], 0.1)
                    if not ready[0]:
                        if process.poll() is not None:
                            break
                        # Check for stdin blocking
                        if self.monitor.check_stdin_blocking(process, last_output_time):
                            process.terminate()
                            state.stdin_blocked_files.append(test_file)
                            break
                        continue
                        
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    continue
                    
                output_lines.append(line)
                last_output_time = time.time()
                
            process.wait()
            state.output = ''.join(output_lines)
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            
            # Check if killed
            if process_info.killed:
                print(f"\n⚠️  {process_info.kill_reason}")
                
        except Exception as e:
            if self.args.debug_runner:
                print(f"[DEBUG] Error running {test_file}: {e}")
            state.output = str(e)
            
        # Parse results for this file
        state.results = self.parser.parse_pytest_output(state.output)
        state.failures = self.parser.extract_failed_tests(state.output)
        
        return state
        
    def _collect_coverage(self) -> Optional[str]:
        """Run a separate coverage collection pass."""
        try:
            print("\nCollecting coverage data...")
            
            # In file-by-file mode, we already have coverage from the test run
            # Just need to generate the final report
            cmd = [
                sys.executable, "-m", "coverage", "report",
                "--show-missing",
                "--skip-covered",
                "--skip-empty"
            ]
            
            # First try to use existing coverage data
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout for report generation
            )
            
            if result.returncode == 0 and result.stdout:
                if self.args.debug_runner:
                    print(f"[DEBUG] Coverage report generated from existing data")
                return result.stdout
            
            # If no existing coverage data, run a quick collection
            print("Running quick coverage collection...")
            cmd = [
                sys.executable, "-m", "pytest",
                str(self.test_dir),
                "--cov=storm_checker",
                "--cov-report=term-missing",
                "--cov-report=html",
                "-q", "--tb=no",
                "--no-header",  # Skip header for cleaner output
                "--maxfail=5"  # Stop after 5 failures to speed up
            ]
            
            # Add pattern filter if specified
            if self.args.pattern:
                cmd.extend(["-k", self.args.pattern])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0 or result.stdout:
                if self.args.debug_runner:
                    print(f"[DEBUG] Coverage output length: {len(result.stdout)} chars")
                    if len(result.stdout) < 1000:
                        print(f"[DEBUG] Coverage output preview:\n{result.stdout}")
                return result.stdout
                
        except subprocess.TimeoutExpired:
            print("⚠️  Coverage collection timed out")
            print("💡 Tip: Use --quick mode for faster coverage or run with --no-coverage")
            return None
        except Exception as e:
            print(f"⚠️  Could not collect coverage: {e}")
            
        return None