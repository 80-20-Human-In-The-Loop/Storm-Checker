#!/usr/bin/env python3
"""MyPy execution and output parsing logic.

This module handles running MyPy type checker, parsing its output,
and converting raw results into structured data for educational analysis.
"""

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .utils import find_python_files


@dataclass
class MypyError:
    """Represents a single MyPy error with parsed components.
    
    Attributes:
        file_path: Path to the file containing the error.
        line_number: Line number where the error occurs.
        column: Column number (optional).
        severity: Error severity level (error, warning, note).
        error_code: MyPy error code (e.g., 'no-untyped-def').
        message: Human-readable error message.
        raw_line: Original raw error line from MyPy.
    """
    file_path: str
    line_number: int
    column: Optional[int]
    severity: str
    error_code: Optional[str]
    message: str
    raw_line: str
    
    def __str__(self) -> str:
        """Return formatted error string."""
        location = f"{self.file_path}:{self.line_number}"
        if self.column is not None:
            location += f":{self.column}"
        
        code_str = f"[{self.error_code}]" if self.error_code else ""
        return f"{location}: {self.severity}: {self.message} {code_str}".strip()


@dataclass
class MypyResult:
    """Result of running MyPy on a set of files.
    
    Attributes:
        success: Whether MyPy ran successfully (no fatal errors).
        errors: List of parsed errors.
        warnings: List of parsed warnings.
        notes: List of parsed notes.
        files_checked: Number of files analyzed.
        execution_time: Time taken to run MyPy in seconds.
        command: The MyPy command that was executed.
        return_code: Process return code.
        raw_output: Complete raw output from MyPy.
    """
    success: bool
    errors: List[MypyError] = field(default_factory=list)
    warnings: List[MypyError] = field(default_factory=list)
    notes: List[MypyError] = field(default_factory=list)
    files_checked: int = 0
    execution_time: float = 0.0
    command: List[str] = field(default_factory=list)
    return_code: int = 0
    raw_output: str = ""
    
    @property
    def total_issues(self) -> int:
        """Total number of all issues (errors + warnings + notes)."""
        return len(self.errors) + len(self.warnings) + len(self.notes)
    
    @property
    def has_errors(self) -> bool:
        """Whether there are any errors."""
        return len(self.errors) > 0
    
    def get_errors_by_file(self) -> Dict[str, List[MypyError]]:
        """Group errors by file path.
        
        Returns:
            Dictionary mapping file paths to lists of errors in that file.
        """
        by_file: Dict[str, List[MypyError]] = {}
        for error in self.errors:
            if error.file_path not in by_file:
                by_file[error.file_path] = []
            by_file[error.file_path].append(error)
        return by_file


class MypyRunner:
    """Handles MyPy execution and result parsing."""
    
    # Regex pattern for parsing MyPy output lines
    # Format: file.py:line:column: severity: message [error-code]
    ERROR_PATTERN = re.compile(
        r'^(?P<file>[^:]+):(?P<line>\d+):(?:(?P<column>\d+):)?\s*'
        r'(?P<severity>error|warning|note):\s*(?P<message>.*?)(?:\s*\[(?P<code>[^\]]+)\])?$'
    )
    
    def __init__(
        self,
        python_executable: Optional[str] = None,
        mypy_executable: Optional[str] = None,
        default_args: Optional[List[str]] = None,
    ):
        """Initialize MyPy runner.
        
        Args:
            python_executable: Path to Python executable. If None, uses sys.executable.
            mypy_executable: Path to MyPy executable. If None, uses 'mypy'.
            default_args: Default arguments to pass to MyPy.
        """
        self.python_executable = python_executable or sys.executable
        self.mypy_executable = mypy_executable or "mypy"
        self.default_args = default_args or [
            "--ignore-missing-imports",
            "--show-error-codes",
            "--no-error-summary",
            "--no-strict-optional",  # More forgiving for learners
        ]
    
    def run_mypy(
        self,
        files: List[Path],
        additional_args: Optional[List[str]] = None,
        timeout: Optional[float] = None,
    ) -> MypyResult:
        """Run MyPy on specified files.
        
        Args:
            files: List of Python files to check.
            additional_args: Extra arguments to pass to MyPy.
            timeout: Maximum time to wait for MyPy to complete.
            
        Returns:
            MypyResult containing parsed results.
            
        Example:
            >>> runner = MypyRunner()
            >>> files = find_python_files(keywords="models")
            >>> result = runner.run_mypy(files)
            >>> print(f"Found {len(result.errors)} errors")
            Found 42 errors
        """
        if not files:
            return MypyResult(
                success=True,
                files_checked=0,
                command=[],
            )
        
        # Build command
        cmd = [self.mypy_executable] + self.default_args
        if additional_args:
            cmd.extend(additional_args)
        cmd.extend(str(f) for f in files)
        
        # Run MyPy
        try:
            import time
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            
            execution_time = time.time() - start_time
            
            # Parse output
            return self.parse_mypy_output(
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                files_checked=len(files),
                execution_time=execution_time,
                command=cmd,
            )
            
        except subprocess.TimeoutExpired:
            return MypyResult(
                success=False,
                files_checked=len(files),
                command=cmd,
                return_code=-1,
                raw_output="MyPy execution timed out",
            )
        except FileNotFoundError:
            return MypyResult(
                success=False,
                files_checked=len(files),
                command=cmd,
                return_code=-1,
                raw_output=f"MyPy executable not found: {self.mypy_executable}",
            )
    
    def parse_mypy_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        files_checked: int,
        execution_time: float,
        command: List[str],
    ) -> MypyResult:
        """Parse MyPy output into structured result.
        
        Args:
            stdout: Standard output from MyPy.
            stderr: Standard error from MyPy.
            return_code: Process return code.
            files_checked: Number of files that were checked.
            execution_time: Time taken to run MyPy.
            command: Command that was executed.
            
        Returns:
            Parsed MypyResult.
        
        TODO: Implement multi-line error parsing for pretty=true support
        When MyPy is configured with pretty=true, it outputs errors in a multi-line
        format like:
            file.py:123: error: Error message here
            type "str", expected "int")  [error-code]
                    actual_code_line_here
                    ^~~~~~~~~~~~~~~~~~~~
        
        Current implementation only handles single-line errors. To support pretty=true:
        1. Detect multi-line error format
        2. Buffer lines until complete error is captured
        3. Extract error code from second line
        4. Parse full error including context lines
        """
        result = MypyResult(
            success=return_code == 0 or return_code == 1,  # 1 = errors found but MyPy ran OK
            files_checked=files_checked,
            execution_time=execution_time,
            command=command,
            return_code=return_code,
            raw_output=stdout + stderr,
        )
        
        # Check for initialization errors that prevent checking
        config_error_patterns = [
            "Error constructing plugin",
            "Source file found twice",
            "errors prevented further checking",
            "Library stubs not installed"
        ]
        
        has_config_error = any(
            pattern in stderr or pattern in stdout 
            for pattern in config_error_patterns
        )
        
        if has_config_error or return_code not in (0, 1):
            result.success = False
            # Parse the actual error message
            error_lines = (stdout + stderr).splitlines()
            for line in error_lines:
                if any(pattern in line for pattern in config_error_patterns):
                    result.errors.append(MypyError(
                        file_path="<configuration>",
                        line_number=0,
                        column=None,
                        severity="error",
                        error_code="config-error",
                        message=line.strip(),
                        raw_line=line
                    ))
            # If we still found no specific error, add a more informative one
            if not result.errors:
                # Try to extract the actual error message
                error_msg = "MyPy configuration error prevented type checking"
                full_output = (stderr + stdout).strip()
                
                # Look for specific known error patterns
                if "is not a valid Python package name" in full_output:
                    # Extract the package name from the error
                    lines = full_output.splitlines()
                    for line in lines:
                        if "is not a valid Python package name" in line:
                            error_msg = line.strip()
                            break
                elif full_output:
                    # Use the first non-empty line as the error message
                    for line in full_output.splitlines():
                        if line.strip():
                            error_msg = line.strip()
                            break
                
                result.errors.append(MypyError(
                    file_path="<configuration>",
                    line_number=0,
                    column=None,
                    severity="error",
                    error_code="config-error",
                    message=error_msg,
                    raw_line=full_output or "Unknown configuration error"
                ))
            # Don't return early - continue parsing to find actual errors too
        
        # Parse each line of output
        lines = stdout.splitlines() + stderr.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip summary lines
            if line.startswith("Found ") or line.startswith("Success:"):
                continue
                
            # Try to parse as error/warning/note
            parsed = self.parse_error_line(line)
            if parsed:
                if parsed.severity == "error":
                    result.errors.append(parsed)
                elif parsed.severity == "warning":
                    result.warnings.append(parsed)
                elif parsed.severity == "note":
                    result.notes.append(parsed)
        
        return result
    
    def parse_error_line(self, line: str) -> Optional[MypyError]:
        """Parse a single error line from MyPy output.
        
        Args:
            line: Raw error line from MyPy.
            
        Returns:
            Parsed MypyError or None if line doesn't match expected format.
            
        Example:
            >>> runner = MypyRunner()
            >>> error = runner.parse_error_line(
            ...     "src/models.py:42:8: error: Function is missing a type annotation [no-untyped-def]"
            ... )
            >>> print(error.error_code)
            no-untyped-def
        """
        match = self.ERROR_PATTERN.match(line)
        if not match:
            return None
            
        return MypyError(
            file_path=match.group("file"),
            line_number=int(match.group("line")),
            column=int(match.group("column")) if match.group("column") else None,
            severity=match.group("severity"),
            error_code=match.group("code"),
            message=match.group("message"),
            raw_line=line,
        )
    
    def filter_ignored_errors(
        self,
        errors: List[MypyError],
        check_source_files: bool = True,
    ) -> Tuple[List[MypyError], List[MypyError]]:
        """Separate genuine errors from intentionally ignored ones.
        
        Args:
            errors: List of MyPy errors to filter.
            check_source_files: Whether to check source files for type: ignore comments.
            
        Returns:
            Tuple of (genuine_errors, ignored_errors).
            
        Example:
            >>> runner = MypyRunner()
            >>> genuine, ignored = runner.filter_ignored_errors(result.errors)
            >>> print(f"Genuine errors: {len(genuine)}, Ignored: {len(ignored)}")
            Genuine errors: 35, Ignored: 7
        """
        if not check_source_files:
            return errors, []
            
        genuine_errors = []
        ignored_errors = []
        
        for error in errors:
            if self._has_type_ignore_comment(error.file_path, error.line_number):
                ignored_errors.append(error)
            else:
                genuine_errors.append(error)
                
        return genuine_errors, ignored_errors
    
    def _has_type_ignore_comment(self, file_path: str, line_number: int) -> bool:
        """Check if a specific line has a type: ignore comment.
        
        Args:
            file_path: Path to the file.
            line_number: Line number to check (1-indexed).
            
        Returns:
            True if the line has a type: ignore comment.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
                if 1 <= line_number <= len(lines):
                    line = lines[line_number - 1]
                    return "# type: ignore" in line
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            pass
        return False
    
    def check_single_file(self, file_path: Path) -> MypyResult:
        """Convenience method to check a single file.
        
        Args:
            file_path: Path to Python file to check.
            
        Returns:
            MypyResult for the single file.
            
        Example:
            >>> runner = MypyRunner()
            >>> result = runner.check_single_file(Path("mymodule.py"))
            >>> if result.has_errors:
            ...     print(f"File has {len(result.errors)} errors")
        """
        return self.run_mypy([file_path])
    
    def check_project(
        self,
        root_path: Path = Path("."),
        keywords: Optional[str] = None,
        exclude_dirs: Optional[Set[str]] = None,
    ) -> MypyResult:
        """Check all Python files in a project.
        
        Args:
            root_path: Project root directory.
            keywords: Optional regex to filter files.
            exclude_dirs: Directories to exclude from checking.
            
        Returns:
            MypyResult for all matching files.
            
        Example:
            >>> runner = MypyRunner()
            >>> result = runner.check_project(keywords="models|views")
            >>> print(f"Checked {result.files_checked} files")
            Checked 23 files
        """
        files = find_python_files(
            root_path=root_path,
            keywords=keywords,
            exclude_dirs=exclude_dirs,
        )
        return self.run_mypy(files)


# TODO: Add support for MyPy configuration files (mypy.ini, pyproject.toml)
# TODO: Add incremental checking support
# TODO: Add support for MyPy plugins (django-stubs, etc.)
# TODO: Add caching of results for unchanged files
# TODO: Add parallel checking support for large projects