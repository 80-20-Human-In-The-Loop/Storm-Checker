#!/usr/bin/env python3
"""
Storm Checker Test Runner
=========================
Beautiful test runner using Storm Checker's CLI components.
"""

import argparse
import sys
import subprocess
import time
import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import json
import random
import re
import threading
import select
import resource
import signal
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.console import Console
from rich.theme import Theme

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from storm_checker.cli.colors import (
        ColorPrinter, print_header, print_success, print_error, print_warning, print_info,
        THEME, PALETTE, RESET, BOLD, DIM, CLEAR_SCREEN, CLEAR_LINE
    )
    from storm_checker.cli.components.border import Border, BorderStyle
    from storm_checker.cli.components.progress_bar import ProgressBar
except ImportError as e:
    print(f"Failed to import storm_checker modules: {e}")
    print("Please ensure storm_checker is properly installed.")
    sys.exit(1)


class TestRunner:
    """Beautiful test runner for Storm Checker."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.start_time = time.time()
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0
        }
        self.failed_tests = []  # Store details of failed tests
        self.coverage_data = {}  # Store coverage information
        self.slow_tests = []  # Store slow test information
        self.slow_test_threshold = args.slow_test_threshold  # Threshold in seconds for slow tests
        self.terminal_width = self._get_terminal_width()
        
        # Safety features
        self.timeout_per_file = getattr(args, 'timeout', 30)  # Default 30s per test file
        self.max_memory_mb = getattr(args, 'max_memory', 2048)  # Default 2GB
        self.safety_enabled = not getattr(args, 'safety_off', False)
        self.monitor_thread = None
        self.process_killed = False
        self.kill_reason = ""
        
    def run(self) -> int:
        """Run the test suite."""
        if not self.args.no_color and not self.args.quiet:
            print(CLEAR_SCREEN)
            
        self._print_header()
        
        # Build pytest command
        pytest_args = self._build_pytest_args()
        
        # Run tests
        if not self.args.quiet:
            print_info("Running tests...")
            print()
            
        result = self._run_pytest(pytest_args)
        
        # Show results
        if not self.args.quiet:
            self._print_results(result)
            
        return result.returncode
    
    def _get_terminal_width(self) -> int:
        """Get terminal width, with fallback."""
        try:
            return shutil.get_terminal_size().columns
        except (OSError, AttributeError):
            return 80  # Fallback width
    
    def _truncate_file_path(self, file_path: str, max_length: int) -> str:
        """Truncate file path to fit within max_length characters."""
        if len(file_path) <= max_length:
            return file_path
        
        # Try to keep the filename and important parts of the directory path
        parts = file_path.split('/')
        if len(parts) > 1:
            filename = parts[-1]
            
            # Always preserve the filename if possible
            if len(filename) < max_length - 4:  # 4 for ".../""
                dir_parts = parts[:-1]
                
                # Try to keep tests/ at the beginning and the immediate parent directory
                if len(dir_parts) >= 2 and dir_parts[0] == 'tests':
                    # Keep "tests" and the immediate parent of the test file
                    parent_dir = dir_parts[-1]
                    potential = f"tests/.../{parent_dir}/{filename}"
                    if len(potential) <= max_length:
                        return potential
                    
                    # If that's still too long, just show tests/.../filename
                    potential = f"tests/.../{filename}"
                    if len(potential) <= max_length:
                        return potential
                
                # General case: show start...end/filename
                dir_space = max_length - len(filename) - 4  # 4 for ".../"
                if dir_space > 5:  # Need some minimum space
                    dir_str = '/'.join(dir_parts)
                    if len(dir_str) > dir_space:
                        # Take first part and last part
                        start_len = dir_space // 2
                        end_len = dir_space - start_len - 3  # 3 for "..."
                        if end_len > 0:
                            truncated = dir_str[:start_len] + "..." + dir_str[-end_len:]
                        else:
                            truncated = dir_str[:dir_space-3] + "..."
                        return f"{truncated}/{filename}"
                    else:
                        return f"{dir_str}/{filename}"
        
        # Fallback: just truncate from the end
        return file_path[:max_length-3] + "..."
    
    def _print_header(self):
        """Print beautiful header."""
        if self.args.quiet:
            return
            
        print_header(
            "⚡ Storm Checker Test Suite ⚡",
            "Running tests with style"
        )
        
        # Show configuration
        border = Border(style=BorderStyle.ROUNDED, color="info", show_left=False)
        config_lines = [
            f"Test Pattern: {self.args.pattern or 'all tests'}",
            f"Markers: {self.args.mark or 'none'}",
            f"Coverage: {'enabled' if self.args.coverage else 'disabled'}",
            f"Verbosity: {self._get_verbosity_label()}",
            f"Dashboard: {'enabled' if self.args.dashboard else 'disabled'}"
        ]
        
        config_box_lines = border.box(
            config_lines,
            width=60,
            padding=2
        )
        config_box = "\n".join(config_box_lines)
        print(config_box)
        print()
        
    def _build_pytest_args(self) -> List[str]:
        """Build pytest command line arguments."""
        args = []
        
        # Add test directory
        args.append("tests/")
        
        # Verbosity
        if self.args.verbose:
            args.append("-vv")
        elif not self.args.quiet:
            args.append("-v")
            
        # Pattern matching
        if self.args.pattern:
            args.extend(["-k", self.args.pattern])
            
        # Markers
        if self.args.mark:
            args.extend(["-m", self.args.mark])
            
        # Coverage
        if self.args.coverage:
            args.extend([
                "--cov=storm_checker",
                "--cov-report=html",
                "--cov-report=term-missing"
            ])
            
        # Failed first
        if self.args.failed_first:
            args.append("--failed-first")
            
        # Add maxfail for quick testing
        if hasattr(self.args, 'maxfail') and self.args.maxfail:
            args.extend(["--maxfail", str(self.args.maxfail)])
            
        # Color output
        if not self.args.no_color:
            args.append("--color=yes")
        else:
            args.append("--color=no")
            
        # Capture output for parsing
        if self.args.dashboard or not self.args.quiet:
            args.append("--tb=short")
            args.append("-r=fEsxXfE")  # Show extra test summary
            
        # Override quiet from pyproject.toml
        # Use -ra to show short test summary but not -q for quiet
        args.append("-o")
        args.append("addopts=-ra")  # Override addopts from config
        
        return args
    
    def _get_memory_usage_mb(self) -> float:
        """Get current process memory usage in MB."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS
        if sys.platform == 'darwin':
            return usage.ru_maxrss / (1024 * 1024)
        else:
            return usage.ru_maxrss / 1024
    
    def _monitor_process(self, process: subprocess.Popen, current_file: str, start_time: float):
        """Monitor process for timeout and memory issues."""
        last_output_time = time.time()
        
        while process.poll() is None and not self.process_killed:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Check timeout
            if elapsed > self.timeout_per_file:
                self.kill_reason = f"Timeout: Test file '{current_file}' exceeded {self.timeout_per_file}s limit"
                self.process_killed = True
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                break
            
            # Check memory usage
            memory_mb = self._get_memory_usage_mb()
            if memory_mb > self.max_memory_mb:
                self.kill_reason = f"Memory limit exceeded: {memory_mb:.0f}MB > {self.max_memory_mb}MB limit"
                self.process_killed = True
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                break
            
            time.sleep(0.5)  # Check every 500ms
    
    def _run_with_progress(self, cmd: List[str], args: List[str]) -> subprocess.CompletedProcess:
        """Run pytest with real-time progress tracking, safety features, and proper colors."""
        
        # Create custom Rich theme matching Storm Checker colors
        storm_theme = Theme({
            "primary": "rgb(65,135,145)",
            "success": "rgb(70,107,93)",
            "error": "rgb(156,82,90)",
            "warning": "rgb(234,182,118)",
            "info": "rgb(88,122,132)",
            "subtle": "rgb(88,122,132) dim"
        })
        console = Console(theme=storm_theme)
        
        # First, get list of test files that will be run
        collect_cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"] + args
        try:
            collect_result = subprocess.run(collect_cmd, capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            print_error("Failed to collect tests (timeout)")
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="Collection timeout")
        
        # Parse test files from collection
        test_files = []
        if collect_result.stdout:
            for line in collect_result.stdout.strip().split('\n'):
                if '.py::' in line and not line.startswith(' '):
                    file_path = line.split('::')[0]
                    if file_path not in test_files:
                        test_files.append(file_path)
        
        # If we couldn't detect files, try to find them directly
        if not test_files:
            # Look for test files in the tests directory
            test_dir = Path("tests")
            if test_dir.exists():
                for py_file in test_dir.rglob("test_*.py"):
                    test_files.append(str(py_file))
        
        if not test_files:
            # Fall back to running all tests at once
            test_files = ["tests/"]
        
        total_files = len(test_files)
        completed_files = 0
        all_output = []
        
        # Reset state
        self.process_killed = False
        self.kill_reason = ""
        
        # Create Rich progress bar with Storm Checker colors
        with Progress(
            SpinnerColumn(style="primary"),
            TextColumn("[primary]{task.description}"),
            BarColumn(complete_style="success", finished_style="success"),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
            
            task = progress.add_task(
                "Running tests...", 
                total=total_files
            )
            
            # Run tests file by file for guaranteed progress updates
            for i, test_file in enumerate(test_files):
                if self.process_killed:
                    break
                    
                display_file = self._truncate_file_path(test_file, 40)
                progress.update(
                    task, 
                    description=f"Testing: {display_file}"
                )
                
                # Run pytest for this specific file
                file_cmd = [sys.executable, "-m", "pytest", test_file, "-v", 
                           "--tb=line", "-o", "log_cli=false"]
                
                # Add other args except the test path
                for arg in args:
                    if not arg.startswith("tests/"):
                        file_cmd.append(arg)
                
                # Run with safety monitoring
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'
                
                file_start_time = time.time()
                
                try:
                    process = subprocess.Popen(
                        file_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,  # Line buffering
                        universal_newlines=True,
                        env=env
                    )
                    
                    # Start monitoring thread if safety is enabled
                    if self.safety_enabled:
                        self.monitor_thread = threading.Thread(
                            target=self._monitor_process,
                            args=(process, test_file, file_start_time)
                        )
                        self.monitor_thread.daemon = True
                        self.monitor_thread.start()
                    
                    # Read output with stdin blocking detection
                    file_output = []
                    last_output_time = time.time()
                    stdin_blocked = False
                    
                    while True:
                        # Use select to check if data is available with timeout
                        try:
                            ready = select.select([process.stdout], [], [], 0.1)
                            
                            if ready[0]:
                                line = process.stdout.readline()
                                if not line:
                                    break
                                    
                                file_output.append(line)
                                last_output_time = time.time()
                            else:
                                # No output available - check if stuck
                                if process.poll() is not None:
                                    # Process finished
                                    break
                                    
                                elapsed_no_output = time.time() - last_output_time
                                if elapsed_no_output > 2.0:  # 2 seconds with no output
                                    # Likely waiting for input
                                    stdin_blocked = True
                                    process.terminate()
                                    time.sleep(0.5)
                                    if process.poll() is None:
                                        process.kill()
                                    
                                    # Add error message
                                    error_msg = f"\n⚠️  Test file '{test_file}' appears to be waiting for user input - skipping\n"
                                    file_output.append(error_msg)
                                    all_output.append(error_msg)
                                    
                                    # Update progress bar
                                    progress.update(
                                        task,
                                        description=f"[error]❌ Blocked: {display_file}"
                                    )
                                    
                                    # Record as error
                                    self.test_results["errors"] += 1
                                    self.failed_tests.append({
                                        "path": test_file,
                                        "error": "Test blocked waiting for input (consider mocking stdin operations)"
                                    })
                                    break
                                    
                        except (OSError, ValueError):
                            # File descriptor closed or invalid
                            break
                    
                    if not stdin_blocked:
                        process.wait()
                        all_output.extend(file_output)
                        
                        # Parse test results from the output
                        # Helper to remove ANSI codes
                        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                        
                        for line in reversed(file_output):
                            # Remove ANSI color codes
                            clean_line = ansi_escape.sub('', line)
                            
                            # Look for summary line like "==== 2 failed, 3 passed, 1 skipped in 0.5s ===="
                            if " in " in clean_line and ("passed" in clean_line or "failed" in clean_line or "skipped" in clean_line):
                                # Extract counts from summary
                                parts = clean_line.split(" in ")[0].strip("= ").split(", ")
                                for part in parts:
                                    part = part.strip()
                                    try:
                                        if "passed" in part:
                                            count = int(part.split()[0])
                                            self.test_results["passed"] += count
                                        elif "failed" in part:
                                            count = int(part.split()[0])
                                            self.test_results["failed"] += count
                                            # Also collect failed test details from output
                                            for output_line in file_output:
                                                clean_output = ansi_escape.sub('', output_line)
                                                if clean_output.startswith("FAILED "):
                                                    test_path = clean_output.split(" - ")[0].replace("FAILED ", "").strip()
                                                    error_msg = clean_output.split(" - ")[1].strip() if " - " in clean_output else "Test failed"
                                                    if test_path not in [f["path"] for f in self.failed_tests]:
                                                        self.failed_tests.append({
                                                            "path": test_path,
                                                            "error": error_msg
                                                        })
                                        elif "skipped" in part:
                                            count = int(part.split()[0])
                                            self.test_results["skipped"] += count
                                        elif "error" in part or "errors" in part:
                                            count = int(part.split()[0])
                                            self.test_results["errors"] += count
                                    except (ValueError, IndexError):
                                        # Skip if we can't parse the number
                                        continue
                                break
                    
                    # Check if process was killed
                    if self.process_killed:
                        print()
                        print_error(f"⚠️  Tests aborted: {self.kill_reason}")
                        if "memory" in self.kill_reason.lower():
                            print_info("💡 Tip: Check for memory leaks or infinite loops in your tests")
                        return subprocess.CompletedProcess(
                            args=cmd,
                            returncode=1,
                            stdout=''.join(all_output),
                            stderr=self.kill_reason
                        )
                    
                    # Track slow tests
                    file_time = time.time() - file_start_time
                    if file_time > self.slow_test_threshold:
                        self.slow_tests.append({
                            'file': test_file,
                            'duration': file_time
                        })
                        # Update progress bar to show slow warning
                        progress.update(
                            task,
                            description=f"[warning]⚠️  Slow: {display_file}"
                        )
                    
                except Exception as e:
                    print()
                    print_error(f"Error running tests for {test_file}: {e}")
                    all_output.append(f"ERROR: {test_file}: {e}\n")
                
                # Update progress
                completed_files += 1
                progress.update(task, advance=1)
                
                # Show memory usage if getting high
                if self.safety_enabled:
                    memory_mb = self._get_memory_usage_mb()
                    if memory_mb > self.max_memory_mb * 0.8:  # 80% of limit
                        progress.update(
                            task,
                            description=f"[warning]⚠️  High memory: {memory_mb:.0f}MB"
                        )
            
            # Final update
            if not self.process_killed:
                progress.update(
                    task, 
                    description="[success]✅ All tests completed",
                    completed=total_files
                )
        
        # Update total count
        self.test_results["total"] = (
            self.test_results["passed"] + 
            self.test_results["failed"] + 
            self.test_results["skipped"]
        )
        
        # Create result
        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=1 if self.test_results["failed"] > 0 or self.process_killed else 0,
            stdout=''.join(all_output),
            stderr=""
        )
        
        return result
    
    def _run_pytest(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run pytest and capture output."""
        if self.args.verbose and not self.args.quiet:
            print(f"{THEME['info']}Running command:{RESET} {' '.join(args)}")
            print()
        
        # Debug: print exact command
        if self.args.debug:
            print(f"[DEBUG] Running: {' '.join(args)}")
        
        # Try to run with subprocess.Popen for real-time output
        try:
            # Run pytest with a reasonable timeout
            start_time = time.time()
            
            # Use sys.executable to ensure we use the right Python
            # Force verbose output to get test names (if not already present)
            if "-v" not in args and not self.args.verbose:
                cmd = [sys.executable, "-m", "pytest", "-v"] + args
            else:
                cmd = [sys.executable, "-m", "pytest"] + args
            
            if self.args.debug:
                print(f"[DEBUG] Full command: {' '.join(cmd)}")
            
            # For verbose mode, just pass through
            if self.args.verbose:
                result = subprocess.run(
                    cmd,
                    text=True,
                    timeout=300
                )
                # Capture output for parsing by running again quickly with --co
                quick_cmd = [sys.executable, "-m", "pytest", "--co", "-q"] + args
                quick_result = subprocess.run(quick_cmd, capture_output=True, text=True, timeout=10)
                result.stdout = quick_result.stdout if quick_result.returncode == 0 else ""
            else:
                # For non-verbose, use real-time progress tracking
                result = self._run_with_progress(cmd, args)
            
            elapsed = time.time() - start_time
            
            if not self.args.quiet:
                print(f"\n✅ Tests completed in {elapsed:.1f}s")
            
            # Check if tests took too long
            if elapsed > 5.0:
                self.slow_tests.append({
                    'file': 'Total test run',
                    'duration': elapsed
                })
            
        except subprocess.TimeoutExpired as e:
            print()
            print_error("Tests timed out after 300 seconds!")
            print_info("This usually indicates a hanging test or infinite loop.")
            if self.args.debug and e.stdout:
                print("[DEBUG] Partial output:")
                # Handle both bytes and string output
                if isinstance(e.stdout, bytes):
                    print(e.stdout.decode('utf-8', errors='replace')[:1000])
                else:
                    print(e.stdout[:1000])
            
            # Create a result from the partial output
            result = subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout=e.stdout.decode('utf-8') if isinstance(e.stdout, bytes) else e.stdout or "",
                stderr=e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else e.stderr or ""
            )
        except Exception as e:
            print()
            print_error(f"Unexpected error running tests: {e}")
            import traceback
            if self.args.debug:
                print("[DEBUG] Traceback:")
                traceback.print_exc()
            result = subprocess.CompletedProcess(
                args=args,
                returncode=1,
                stdout="",
                stderr=str(e)
            )
        
        # Parse results
        if result.stdout:
            self._parse_results(result.stdout)
        
        return result
    
    def _parse_results(self, output: str):
        """Parse pytest output for statistics."""
        lines = output.splitlines()
        
        # Helper function to remove ANSI escape codes
        import re
        def remove_ansi_codes(text):
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', text)
        
        # Parse failed test details from short summary section
        in_summary = False
        for line in lines:
            clean_line = remove_ansi_codes(line)
            
            # Start of short summary info
            if "short test summary info" in clean_line:
                in_summary = True
                continue
                
            # End of summary (next section starts with =)
            if in_summary and clean_line.startswith("="):
                in_summary = False
                continue
                
            # Parse FAILED lines
            if in_summary and clean_line.startswith("FAILED"):
                # Format: "FAILED tests/file.py::TestClass::test_method - AssertionError: message"
                parts = clean_line.split(" - ", 1)
                if parts:
                    test_path = parts[0].replace("FAILED ", "").strip()
                    error_msg = parts[1] if len(parts) > 1 else "Test failed"
                    self.failed_tests.append({
                        "path": test_path,
                        "error": error_msg
                    })
        
        # Look for the summary line at the end 
        # Format: "========================= 2 failed, 96 passed in 0.26s ========================="
        for line in reversed(lines):
            line = line.strip()
            
            # Remove ANSI codes first, then leading/trailing equals signs
            clean_line = remove_ansi_codes(line).strip("= ")
            
            if " in " in clean_line and ("passed" in clean_line or "failed" in clean_line or "error" in clean_line or "skipped" in clean_line):
                # Parse the summary line
                # Format: "X failed, Y passed in Z.ZZs" or "X passed in Y.YYs"
                parts = clean_line.split(" in ")[0].split(", ")
                
                for part in parts:
                    part = part.strip()
                    if part.endswith(" passed"):
                        self.test_results["passed"] = int(part.split()[0])
                    elif part.endswith(" failed"):
                        self.test_results["failed"] = int(part.split()[0])
                    elif part.endswith(" error") or part.endswith(" errors"):
                        self.test_results["errors"] = int(part.split()[0])
                    elif part.endswith(" skipped"):
                        self.test_results["skipped"] = int(part.split()[0])
                break
        
        # Also count test result markers in the progress output
        # Look for lines like "tests/cli/components/test_border.py .....F..F........F."
        test_count = 0
        for line in lines:
            clean_line = remove_ansi_codes(line)
            if '.py' in clean_line and any(char in clean_line for char in ['.', 'F', 's', 'E', 'x']):
                # Look for test result markers after .py filename
                # Find the last occurrence of .py to handle paths with .py in them
                py_index = clean_line.rfind('.py')
                if py_index != -1:
                    # Get everything after the .py and any whitespace
                    after_py = clean_line[py_index + 3:].strip()
                    # Remove percentage indicators like [100%]
                    result_chars = re.sub(r'\[.*?\]', '', after_py).strip()
                    # Count valid test result characters
                    test_count += len([c for c in result_chars if c in '.FsExX'])
        
        # Use the count from summary if available, otherwise use character counting
        calculated_total = sum([
            self.test_results["passed"],
            self.test_results["failed"],
            self.test_results["errors"],
            self.test_results["skipped"]
        ])
        
        # If we have a calculated total from the summary, use that
        # Otherwise fall back to character counting
        if calculated_total > 0:
            self.test_results["total"] = calculated_total
        else:
            self.test_results["total"] = test_count
        
    def _print_results(self, result: subprocess.CompletedProcess):
        """Print test results beautifully."""
        elapsed_time = time.time() - self.start_time
        
        if self.args.dashboard:
            self._print_dashboard(elapsed_time)
        else:
            self._print_summary(elapsed_time)
            
        # Show coverage report
        if self.args.coverage and result.returncode == 0:
            self._parse_coverage_data(result.stdout)
            if self.coverage_data:
                print()
                self._print_coverage_report()
            print()
            print_info(f"📝 Full coverage report at: {ColorPrinter.primary('htmlcov/index.html', bold=True)}")
            
        # Show detailed failure information
        if result.returncode != 0 and not self.args.verbose:
            print()
            self._print_failures()
            
        # Show slow tests summary
        if self.slow_tests:
            print()
            self._print_slow_tests_summary()
            
        if result.returncode != 0 and not self.args.verbose:
            print()
            print_info(f"💡 Tip: Run {ColorPrinter.primary('python tests/run_tests.py -v')} for detailed output")
            if self.failed_tests and len(self.failed_tests) == 1:
                test = self.failed_tests[0]
                test_path = test["path"]
                print_info(f"    Or debug single test: {ColorPrinter.primary(f'pytest {test_path} -vv')}")
                
    def _print_summary(self, elapsed_time: float):
        """Print simple test summary."""
        print()
        border = Border(
            style=BorderStyle.DOUBLE,
            color="success" if self.test_results["failed"] == 0 else "error",
            show_left=False
        )
        
        # Build summary lines
        lines = [
            f"Total Tests: {self.test_results['total']}"
        ]
        
        if self.test_results["passed"] > 0:
            lines.append(f"✅ Passed: {ColorPrinter.success(str(self.test_results['passed']))}")
        if self.test_results["failed"] > 0:
            lines.append(f"❌ Failed: {ColorPrinter.error(str(self.test_results['failed']))}")
        if self.test_results["errors"] > 0:
            lines.append(f"💥 Errors: {ColorPrinter.error(str(self.test_results['errors']))}")
        if self.test_results["skipped"] > 0:
            lines.append(f"⏭️  Skipped: {ColorPrinter.warning(str(self.test_results['skipped']))}")
            
        lines.append("")
        lines.append(f"⏱️  Time: {elapsed_time:.2f}s")
        
        # Success rate
        if self.test_results["total"] > 0:
            success_rate = (self.test_results["passed"] / self.test_results["total"]) * 100
            lines.append(f"📊 Success Rate: {success_rate:.1f}%")
        
        summary_box_lines = border.box(
            lines,
            width=50,
            padding=2
        )
        summary_box = "\n".join(summary_box_lines)
        print(summary_box)
        
    def _print_dashboard(self, elapsed_time: float):
        """Print beautiful dashboard view of results."""
        print()
        print_header("Test Results Dashboard", None)
        
        # Create progress bars for each metric
        if self.test_results["total"] > 0:
            # Success rate bar
            success_rate = (self.test_results["passed"] / self.test_results["total"]) * 100
            success_bar = ProgressBar(
                width=50,
                style="blocks",
                color_filled="success" if success_rate >= 80 else "warning",
                show_percentage=True
            )
            success_bar_str = success_bar.render(success_rate, 100, "Success Rate")
            print(success_bar_str)
            print()
            
            # Individual metrics
            metrics_border = Border(style=BorderStyle.ROUNDED, color="primary", show_left=False)
            metrics = [
                ("Passed", self.test_results["passed"], THEME['success'], "✅"),
                ("Failed", self.test_results["failed"], THEME['error'], "❌"),
                ("Errors", self.test_results["errors"], THEME['error'], "💥"),
                ("Skipped", self.test_results["skipped"], THEME['warning'], "⏭️"),
            ]
            
            metric_lines = []
            for name, count, color, icon in metrics:
                if count > 0:
                    bar = ProgressBar(
                        width=40,
                        style="dots",
                        color_filled=color.split('_')[0] if '_' in str(color) else "primary",
                        show_fraction=True
                    )
                    bar_str = bar.render(count, self.test_results["total"], f"{icon} {name}")
                    metric_lines.append(bar_str)
                    
            if metric_lines:
                metrics_box_lines = metrics_border.box(
                    metric_lines,
                    width=60,
                    padding=1
                )
                print("\n".join(metrics_box_lines))
                
            # Performance stats
            print()
            perf_border = Border(style=BorderStyle.SINGLE, color="info", show_left=False)
            tests_per_sec = self.test_results["total"] / elapsed_time if elapsed_time > 0 else 0
            avg_time_ms = elapsed_time / self.test_results["total"] * 1000 if self.test_results["total"] > 0 else 0
            
            perf_lines = [
                f"Total Time: {ColorPrinter.info(f'{elapsed_time:.2f}s')}",
                f"Tests/Second: {ColorPrinter.info(f'{tests_per_sec:.1f}')}",
                f"Avg Time/Test: {ColorPrinter.info(f'{avg_time_ms:.1f}ms')}"
            ]
            
            perf_box_lines = perf_border.box(
                perf_lines,
                width=40,
                padding=2
            )
            print("\n".join(perf_box_lines))
            
    def _get_verbosity_label(self) -> str:
        """Get verbosity label for display."""
        if self.args.quiet:
            return "quiet"
        elif self.args.verbose:
            return "verbose"
        else:
            return "normal"
    
    def _parse_coverage_data(self, output: str):
        """Parse coverage data from pytest output."""
        lines = output.splitlines()
        in_coverage = False
        coverage_started = False
        
        for line in lines:
            # Look for coverage section
            if "coverage:" in line.lower() and "platform" in line.lower():
                in_coverage = True
                continue
            
            if in_coverage:
                # Skip header lines
                if line.startswith("Name") or line.startswith("-"):
                    coverage_started = True
                    continue
                
                if coverage_started and line.strip():
                    # End of coverage section
                    if line.startswith("TOTAL") or "passed" in line or "failed" in line:
                        if line.startswith("TOTAL"):
                            # Parse total line
                            parts = line.split()
                            if len(parts) >= 4:
                                self.coverage_data["_total"] = {
                                    "stmts": int(parts[1]),
                                    "miss": int(parts[2]),
                                    "cover": float(parts[3].rstrip("%"))
                                }
                        break
                    
                    # Parse file coverage line
                    # Format: "path/file.py    100    20    80%    12-15, 23, 45-50"
                    match = re.match(r'^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)%(?:\s+(.*))?', line)
                    if match:
                        filepath = match.group(1)
                        stmts = int(match.group(2))
                        miss = int(match.group(3))
                        cover = int(match.group(4))
                        missing_lines = match.group(5) if match.group(5) else ""
                        
                        self.coverage_data[filepath] = {
                            "stmts": stmts,
                            "miss": miss,
                            "cover": cover,
                            "missing_lines": self._parse_missing_lines(missing_lines)
                        }
    
    def _parse_missing_lines(self, missing_str: str) -> List[int]:
        """Parse missing line numbers from coverage output."""
        if not missing_str:
            return []
        
        lines = []
        parts = missing_str.split(",")
        
        for part in parts:
            part = part.strip()
            if "-" in part:
                # Range like "12-15"
                start, end = part.split("-")
                lines.extend(range(int(start), int(end) + 1))
            elif part.isdigit():
                # Single line
                lines.append(int(part))
        
        return lines
    
    def _print_coverage_report(self):
        """Print beautiful coverage report."""
        print_header("📊 Coverage Report", None)
        
        # Calculate overall coverage
        total_data = self.coverage_data.get("_total", {})
        if total_data:
            overall_coverage = total_data.get("cover", 0)
            color = "success" if overall_coverage >= 80 else "warning" if overall_coverage >= 50 else "error"
            
            # Overall coverage with progress bar
            progress = ProgressBar(
                width=20,
                style="blocks",
                color_filled=color,
                show_percentage=False
            )
            bar = progress.render(overall_coverage, 100, "")
            coverage_text = f'{overall_coverage:.1f}%'
            if color == "success":
                colored_coverage = ColorPrinter.success(coverage_text)
            elif color == "warning":
                colored_coverage = ColorPrinter.warning(coverage_text)
            else:
                colored_coverage = ColorPrinter.error(coverage_text)
            print(f"\n✨ Overall Coverage: {colored_coverage} {bar}\n")
        
        # Collect all files with their full paths and sort by coverage
        all_files = []
        for filepath, data in self.coverage_data.items():
            if filepath == "_total":
                continue
            all_files.append((filepath, data))
        
        # Sort all files by coverage percentage (descending)
        all_files.sort(key=lambda x: x[1]["cover"], reverse=True)
        
        # Display files with full paths
        for filepath, data in all_files:
            cover = data["cover"]
            
            # Create progress bar
            color = "success" if cover >= 80 else "warning" if cover >= 50 else "error"
            progress = ProgressBar(
                width=20,
                style="blocks",
                color_filled=color,
                show_percentage=False
            )
            bar = progress.render(cover, 100, "")
            
            # Format filepath with padding
            padded_filepath = f"{filepath:<40}"
            
            if cover == 100:
                print(f"{padded_filepath} {bar} {ColorPrinter.success('100%')}  ✅")
            else:
                coverage_pct = f'{cover:3d}%'
                if color == "success":
                    colored_pct = ColorPrinter.success(coverage_pct)
                elif color == "warning":
                    colored_pct = ColorPrinter.warning(coverage_pct)  
                else:
                    colored_pct = ColorPrinter.error(coverage_pct)
                print(f"{padded_filepath} {bar} {colored_pct}  ")
                
                # Show missing lines and random code snippet
                missing = data["missing_lines"]
                if missing:
                    # Format missing lines compactly
                    missing_str = self._format_missing_lines(missing)
                    print(f"    {DIM}Missing: {missing_str}{RESET}")
                    
                    # Try to show a random uncovered line
                    code_line = self._get_random_uncovered_line(filepath, missing)
                    if code_line:
                        print(f"    💡 {DIM}Line {code_line[0]}: {ColorPrinter.warning(code_line[1])}{RESET}")
        
        print()  # Space after file list
        
        # Show quick wins
        quick_wins = []
        for filepath, data in self.coverage_data.items():
            if filepath != "_total" and 90 <= data["cover"] < 100:
                quick_wins.append((filepath, data["miss"]))
        
        if quick_wins:
            quick_wins.sort(key=lambda x: x[1])
            print(f"{ColorPrinter.primary('🎯 Quick Wins', bold=True)} (files close to 100%):")
            for filepath, miss in quick_wins[:3]:
                print(f"  • {filepath} - Just {ColorPrinter.success(str(miss))} line{'s' if miss != 1 else ''} to go!")
            print()
    
    def _format_missing_lines(self, lines: List[int]) -> str:
        """Format missing line numbers compactly."""
        if not lines:
            return ""
        
        lines = sorted(lines)
        ranges = []
        start = lines[0]
        end = lines[0]
        
        for line in lines[1:]:
            if line == end + 1:
                end = line
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = line
                end = line
        
        # Add last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        # Limit to first 5 ranges
        if len(ranges) > 5:
            return ", ".join(ranges[:5]) + "..."
        
        return ", ".join(ranges)
    
    def _get_random_uncovered_line(self, filepath: str, missing_lines: List[int]) -> Optional[Tuple[int, str]]:
        """Get a random uncovered line from the file."""
        if not missing_lines:
            return None
        
        # Try to read the file
        try:
            full_path = Path.cwd() / filepath
            if not full_path.exists():
                return None
            
            with open(full_path, 'r') as f:
                lines = f.readlines()
            
            # Filter to valid line numbers
            valid_missing = [n for n in missing_lines if 0 < n <= len(lines)]
            if not valid_missing:
                return None
            
            # Pick a random line
            line_num = random.choice(valid_missing)
            line_content = lines[line_num - 1].strip()
            
            # Skip empty lines or comments
            if not line_content or line_content.startswith("#"):
                # Try another line
                for _ in range(min(5, len(valid_missing))):
                    line_num = random.choice(valid_missing)
                    line_content = lines[line_num - 1].strip()
                    if line_content and not line_content.startswith("#"):
                        break
            
            # Truncate if too long
            if len(line_content) > 50:
                line_content = line_content[:47] + "..."
            
            return (line_num, line_content)
            
        except Exception:
            return None
    
    def _print_slow_tests_summary(self):
        """Print summary of slow test files."""
        # Sort by duration descending
        sorted_slow_tests = sorted(self.slow_tests, key=lambda x: x['duration'], reverse=True)
        
        print_warning(f"\n🐌 {len(self.slow_tests)} Slow Test File{'s' if len(self.slow_tests) > 1 else ''}:\n")
        
        for test in sorted_slow_tests[:5]:  # Show top 5 slowest
            print(f"  {ColorPrinter.warning(test['file'])} - {test['duration']:.2f}s")
        
        if len(sorted_slow_tests) > 5:
            print(f"  ... and {len(sorted_slow_tests) - 5} more")
        
        print()
        print_info(f"💡 Tip: Run {ColorPrinter.primary('pytest --durations=10')} to see detailed per-test execution times")
        print_info(f"    Or use {ColorPrinter.primary('pytest --durations=0')} to see all test durations")
    
    def _print_failures(self):
        """Print detailed failure information."""
        if not self.failed_tests:
            print_error("Tests failed but no details available. Run with -v for more info.")
            return
            
        # Group failures by file
        failures_by_file = {}
        for failure in self.failed_tests:
            file_path = failure["path"].split("::")[0]
            if file_path not in failures_by_file:
                failures_by_file[file_path] = []
            failures_by_file[file_path].append(failure)
        
        print_error(f"\n❌ {len(self.failed_tests)} Test Failure{'s' if len(self.failed_tests) > 1 else ''}:\n")
        
        for file_path, failures in failures_by_file.items():
            print(f"{ColorPrinter.error(file_path, bold=True)}")
            
            for failure in failures:
                # Extract test name from path
                test_parts = failure["path"].split("::")[1:]
                test_name = "::".join(test_parts) if test_parts else "unknown"
                
                print(f"  {ColorPrinter.error('✗')} {test_name}")
                print(f"    {DIM}{failure['error']}{RESET}")
            print()  # Blank line between files


def main():
    """Main entry point."""
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
    
    args = parser.parse_args()
    
    # Run tests
    runner = TestRunner(args)
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())