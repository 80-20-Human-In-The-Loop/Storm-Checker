"""
Result Parser for Test Runner
==============================
Parses pytest and coverage output to extract test results and metrics.
"""

import re
from typing import List, Dict, Tuple, Optional
from .models import TestResult, TestFailure, SlowTest, CoverageInfo


class ResultParser:
    """Parses test execution output to extract results and metrics."""
    
    def __init__(self):
        # Regex patterns for parsing
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self.test_summary_pattern = re.compile(
            r'(\d+)\s+(passed|failed|error|errors|skipped)',
            re.IGNORECASE
        )
        # Updated pattern to handle full file paths and varied spacing
        self.coverage_line_pattern = re.compile(
            r'^(.+?\.py)\s+(\d+)\s+(\d+)\s+(\d+)%\s*(.*)$'
        )
        self.failed_test_pattern = re.compile(r'^FAILED\s+(.+?)\s+-\s+(.+)$')
        
    def remove_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape codes from text."""
        return self.ansi_escape.sub('', text)
        
    def parse_pytest_output(self, output: str) -> TestResult:
        """Parse pytest output to extract test counts and results."""
        result = TestResult()
        lines = output.splitlines()
        
        # Look for the summary line at the end
        for line in reversed(lines):
            clean_line = self.remove_ansi_codes(line).strip("= ")
            
            if " in " in clean_line and any(word in clean_line for word in ["passed", "failed", "error", "skipped"]):
                # Parse summary line like "2 failed, 96 passed in 0.26s"
                parts = clean_line.split(" in ")[0].split(", ")
                
                for part in parts:
                    part = part.strip()
                    self._parse_test_count(part, result)
                    
                # Extract elapsed time if present
                if " in " in clean_line:
                    time_part = clean_line.split(" in ")[1].rstrip("s")
                    try:
                        result.elapsed_time = float(time_part)
                    except ValueError:
                        pass
                break
                
        # Also count test markers in progress output
        test_marker_count = self._count_test_markers(lines)
        
        # Use the marker count if we found any
        if test_marker_count > 0:
            result.total = test_marker_count
            # If we didn't find summary counts but have test markers, 
            # assume all passed if no explicit failures found
            if result.passed == 0 and result.failed == 0 and result.errors == 0:
                result.passed = test_marker_count
        elif result.total == 0:
            result.update_total()
            
        return result
        
    def _parse_test_count(self, text: str, result: TestResult):
        """Parse a single test count like '96 passed'."""
        try:
            if text.endswith(" passed"):
                result.passed = int(text.split()[0])
            elif text.endswith(" failed"):
                result.failed = int(text.split()[0])
            elif text.endswith(" error") or text.endswith(" errors"):
                result.errors = int(text.split()[0])
            elif text.endswith(" skipped"):
                result.skipped = int(text.split()[0])
        except (ValueError, IndexError):
            pass
            
    def _count_test_markers(self, lines: List[str]) -> int:
        """Count test markers in pytest progress output."""
        test_count = 0
        
        for line in lines:
            clean_line = self.remove_ansi_codes(line)
            
            # Look for lines with test result markers after .py
            if '.py' in clean_line and any(char in clean_line for char in ['.', 'F', 's', 'E', 'x']):
                py_index = clean_line.rfind('.py')
                if py_index != -1:
                    after_py = clean_line[py_index + 3:].strip()
                    # Remove percentage indicators
                    result_chars = re.sub(r'\[.*?\]', '', after_py).strip()
                    # Count valid test result characters
                    test_count += len([c for c in result_chars if c in '.FsExX'])
                    
        return test_count
        
    def extract_failed_tests(self, output: str) -> List[TestFailure]:
        """Extract information about failed tests from output."""
        failures = []
        lines = output.splitlines()
        
        in_summary = False
        for line in lines:
            clean_line = self.remove_ansi_codes(line)
            
            # Check for short summary section
            if "short test summary info" in clean_line:
                in_summary = True
                continue
                
            # End of summary
            if in_summary and clean_line.startswith("="):
                in_summary = False
                continue
                
            # Parse FAILED lines
            if in_summary and clean_line.startswith("FAILED"):
                match = self.failed_test_pattern.match(clean_line)
                if match:
                    test_path = match.group(1).strip()
                    error_msg = match.group(2).strip()
                    failures.append(TestFailure(path=test_path, error=error_msg))
                    
        return failures
        
    def extract_slow_tests(self, output: str, threshold: float = 1.0) -> List[SlowTest]:
        """Extract information about slow tests from output."""
        slow_tests = []
        lines = output.splitlines()
        
        # Look for slowest durations report
        in_slowest = False
        for line in lines:
            clean_line = self.remove_ansi_codes(line)
            
            if "slowest" in clean_line.lower() and "duration" in clean_line.lower():
                in_slowest = True
                continue
                
            if in_slowest:
                # Parse lines like "5.43s call tests/test_foo.py::test_something"
                match = re.match(r'(\d+\.?\d*)\s*s\s+call\s+(.+)', clean_line)
                if match:
                    duration = float(match.group(1))
                    test_path = match.group(2)
                    
                    if duration >= threshold:
                        file_path = test_path.split("::")[0] if "::" in test_path else test_path
                        test_name = "::".join(test_path.split("::")[1:]) if "::" in test_path else None
                        slow_tests.append(SlowTest(
                            file=file_path,
                            duration=duration,
                            test_name=test_name
                        ))
                        
                # Stop when we hit the next section
                if clean_line.startswith("="):
                    break
                    
        return slow_tests
        
    def parse_coverage_output(self, output: str) -> Dict[str, CoverageInfo]:
        """Parse coverage report output."""
        coverage_data = {}
        lines = output.splitlines()
        
        in_coverage = False
        for line in lines:
            clean_line = self.remove_ansi_codes(line).strip()
            
            # Look for coverage table header
            if "Name" in clean_line and "Stmts" in clean_line and "Cover" in clean_line:
                in_coverage = True
                continue
                
            # Skip separator lines
            if clean_line.startswith("-") and in_coverage:
                continue
                
            # End of coverage table
            if in_coverage and (clean_line.startswith("TOTAL") or clean_line.startswith("=")):
                # Parse TOTAL line if present
                if clean_line.startswith("TOTAL"):
                    # TOTAL line has different format: "TOTAL    2847   1186    58%"
                    parts = clean_line.split()
                    if len(parts) >= 4:
                        try:
                            statements = int(parts[1])
                            missed = int(parts[2])
                            coverage_percent = float(parts[3].rstrip('%'))
                            coverage_data["_total"] = CoverageInfo(
                                filepath="TOTAL",
                                statements=statements,
                                missed=missed,
                                coverage_percent=coverage_percent,
                                missing_lines=[]
                            )
                        except (ValueError, IndexError):
                            pass
                in_coverage = False
                continue
                
            # Parse coverage lines - handle both full paths and module paths
            if in_coverage and clean_line and not clean_line.startswith("Name"):
                # Try to parse with flexible whitespace
                match = self.coverage_line_pattern.match(clean_line)
                if match:
                    info = self._parse_coverage_line(match)
                    # Simplify the filepath for display
                    simplified_path = self._simplify_filepath(info.filepath)
                    coverage_data[simplified_path] = info
                    
        return coverage_data
        
    def _simplify_filepath(self, filepath: str) -> str:
        """Simplify file path for display."""
        # Remove common prefix paths
        if "/storm-checker/" in filepath:
            # Get everything after storm-checker/
            parts = filepath.split("/storm-checker/")
            if len(parts) > 1:
                return parts[-1]
        
        # If it's already a module path, keep it
        if not filepath.startswith("/"):
            return filepath
            
        # Otherwise, try to extract just the relative path
        if "/storm_checker/" in filepath:
            parts = filepath.split("/storm_checker/")
            if len(parts) > 1:
                return "storm_checker/" + parts[-1]
                
        return filepath
    
    def _parse_coverage_line(self, match) -> CoverageInfo:
        """Parse a single coverage line from regex match."""
        filepath = match.group(1).strip()
        statements = int(match.group(2))
        missed = int(match.group(3))
        coverage_percent = float(match.group(4))
        missing_lines_str = match.group(5).strip() if match.group(5) else ""
        
        missing_lines = self.parse_missing_lines(missing_lines_str)
        
        return CoverageInfo(
            filepath=filepath,
            statements=statements,
            missed=missed,
            coverage_percent=coverage_percent,
            missing_lines=missing_lines
        )
        
    def parse_missing_lines(self, missing_str: str) -> List[int]:
        """Parse missing line numbers from coverage output."""
        if not missing_str or missing_str == "Missing":
            return []
            
        lines = []
        parts = missing_str.split(", ")
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            if "-" in part:
                # Range like "10-15"
                try:
                    start, end = part.split("-")
                    lines.extend(range(int(start), int(end) + 1))
                except (ValueError, IndexError):
                    pass
            else:
                # Single line number
                try:
                    lines.append(int(part))
                except ValueError:
                    pass
                    
        return sorted(lines)
        
    def parse_file_output(self, output: List[str], test_file: str) -> Tuple[TestResult, List[TestFailure]]:
        """Parse output from a single test file execution."""
        result = TestResult()
        failures = []
        
        # Join lines for full parsing
        full_output = ''.join(output)
        
        # Extract test counts
        file_result = self.parse_pytest_output(full_output)
        result.passed += file_result.passed
        result.failed += file_result.failed
        result.skipped += file_result.skipped
        result.errors += file_result.errors
        
        # Extract failures specific to this file
        file_failures = self.extract_failed_tests(full_output)
        for failure in file_failures:
            if test_file in failure.path:
                failures.append(failure)
                
        return result, failures
        
    def detect_stdin_blocking(self, output: str) -> bool:
        """Detect if tests are blocked waiting for stdin input."""
        indicators = [
            "waiting for user input",
            "blocked on stdin",
            "input()",
            "sys.stdin.read",
            "KeyboardInterrupt"
        ]
        
        clean_output = self.remove_ansi_codes(output.lower())
        return any(indicator in clean_output for indicator in indicators)