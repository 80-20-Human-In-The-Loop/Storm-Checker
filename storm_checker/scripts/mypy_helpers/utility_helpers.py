#!/usr/bin/env python3
"""
Utility Helper Functions for Storm-Checker
==========================================
Utility functions for configuration, tracking, and data processing.
"""

import json
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from storm_checker.cli.colors import print_warning, print_info
from storm_checker.logic.mypy_runner import MypyResult, MypyError
from storm_checker.logic.progress_tracker import ProgressTracker


def check_pyproject_config() -> Tuple[bool, bool]:
    """
    Check for pyproject.toml existence and configuration issues.
    
    Returns:
        tuple: (pyproject_exists, has_pretty_true_issue)
    """
    pyproject_exists = Path("pyproject.toml").exists()
    has_pretty_true = False
    
    if pyproject_exists:
        try:
            with open("pyproject.toml", "r") as f:
                content = f.read()
                if "pretty = true" in content or "pretty=true" in content:
                    has_pretty_true = True
        except Exception:
            pass  # Ignore parsing errors
    
    return pyproject_exists, has_pretty_true


def warn_about_pretty_true(json_mode: bool = False) -> None:
    """Print warning about pretty=true configuration if not in JSON mode."""
    if not json_mode:
        print_warning("⚠️  PRETTY=TRUE DETECTED! MUST BE FALSE FOR TOOL TO FUNCTION PROPERLY")
        print_info("Set 'pretty = false' in [tool.mypy] section of pyproject.toml")
        print()


def create_config_error() -> MypyError:
    """Create a configuration error for missing pyproject.toml."""
    return MypyError(
        file_path="<configuration>",
        line_number=0,
        column=None,
        severity="error",
        error_code="config-error",
        message="No pyproject.toml found. Create one for better MyPy configuration and type checking control.",
        raw_line="Missing pyproject.toml"
    )


def filter_and_categorize_errors(
    errors: List[MypyError],
    runner
) -> Tuple[List[MypyError], List[MypyError], List[MypyError], List[MypyError]]:
    """
    Filter and categorize errors into different types.
    
    Args:
        errors: List of MyPy errors
        runner: MypyRunner instance for filtering
        
    Returns:
        tuple: (genuine_errors, ignored_errors, config_errors, regular_errors)
    """
    # Filter ignored errors
    genuine_errors, ignored_errors = runner.filter_ignored_errors(errors)
    
    # Separate configuration errors from regular errors
    config_errors = [e for e in genuine_errors if e.file_path == "<configuration>"]
    regular_errors = [e for e in genuine_errors if e.file_path != "<configuration>"]
    
    return genuine_errors, ignored_errors, config_errors, regular_errors


def setup_tracking_session(
    tracker: ProgressTracker,
    no_track: bool = False
) -> None:
    """
    Set up a tracking session if tracking is enabled.
    
    Args:
        tracker: ProgressTracker instance
        no_track: Whether to skip tracking
    """
    if not no_track:
        tracker.start_session()


def end_tracking_session(
    tracker: ProgressTracker,
    result: MypyResult,
    files: List[Path],
    no_track: bool = False
) -> None:
    """
    End tracking session and record metrics.
    
    Args:
        tracker: ProgressTracker instance
        result: MyPy result
        files: List of checked files
        no_track: Whether to skip tracking
    """
    if not no_track:
        # Update session statistics
        if hasattr(tracker, 'update_session_stats'):
            # Calculate errors fixed if we have a current session
            errors_fixed = None
            if hasattr(tracker, 'current_session') and tracker.current_session:
                if hasattr(tracker.current_session, 'errors_found'):
                    # If we had errors before and now have fewer, we fixed some
                    initial_errors = getattr(tracker.current_session, 'errors_found', 0)
                    current_errors = len(result.errors)
                    if initial_errors > current_errors:
                        errors_fixed = initial_errors - current_errors
            
            # Update the session stats
            tracker.update_session_stats(
                files_checked=len(files),
                errors_found=len(result.errors),
                errors_fixed=errors_fixed
            )
        
        # Record error types encountered
        error_codes = set()
        for error in result.errors:
            if error.error_code:
                error_codes.add(error.error_code)
        
        # Track learned error types (if method exists)
        if hasattr(tracker, 'record_error_type_encountered'):
            for error_code in error_codes:
                tracker.record_error_type_encountered(error_code)
        
        # End session with time (v2 API expects float)
        if hasattr(tracker, 'end_session'):
            # Use execution time from result
            tracker.end_session(result.execution_time if hasattr(result, 'execution_time') else 0.0)
        
        # Mark mastered files (if method exists)
        if hasattr(tracker, 'mark_file_mastered'):
            for file_path in files:
                file_errors = get_file_errors(result, str(file_path))
                if not file_errors:
                    tracker.mark_file_mastered(str(file_path))


def get_file_errors(result: MypyResult, file_path: str) -> List[MypyError]:
    """
    Get all errors for a specific file.
    
    Args:
        result: MyPy result containing all errors
        file_path: Path to the file
        
    Returns:
        list: List of errors for the specified file
    """
    return [e for e in result.errors if e.file_path == file_path]


def process_json_output(
    result: MypyResult,
    analysis,
    ignored_count: int
) -> str:
    """
    Process and format results as JSON output.
    
    Args:
        result: MyPy result
        analysis: Analysis result
        ignored_count: Number of ignored errors
        
    Returns:
        str: JSON formatted string
    """
    output = {
        "files_checked": result.files_checked,
        "total_issues": result.total_issues,
        "errors": len(result.errors),
        "warnings": len(result.warnings),
        "ignored": ignored_count,
        "complexity_score": analysis.complexity_score,
        "categories": {k: len(v) for k, v in analysis.by_category.items()},
        "suggested_tutorials": analysis.suggested_tutorials[:3],
    }
    return json.dumps(output, indent=2)


def create_analysis_result(
    result: MypyResult,
    config_errors: List[MypyError]
) -> MypyResult:
    """
    Create a modified MyPy result for analysis (without config errors).
    
    Args:
        result: Original MyPy result
        config_errors: List of configuration errors to exclude
        
    Returns:
        MypyResult: Modified result without config errors
    """
    regular_errors = [e for e in result.errors if e.file_path != "<configuration>"]
    
    return MypyResult(
        success=result.success,
        errors=regular_errors,
        warnings=result.warnings,
        notes=result.notes,
        files_checked=result.files_checked,
        execution_time=result.execution_time,
        command=result.command,
        return_code=result.return_code,
        raw_output=result.raw_output
    )


def should_exit_early(args) -> Optional[int]:
    """
    Check if we should exit early based on special modes.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Optional[int]: Exit code if should exit, None otherwise
    """
    # Check for tutorial subcommand
    if hasattr(args, 'subcommand') and args.subcommand == 'tutorial':
        from storm_checker.scripts.mypy_tutorial import main as tutorial_main
        # Restore the remaining args for tutorial parser
        import sys
        remaining = sys.argv[2:]  # Skip script name and 'tutorial'
        sys.argv = ['mypy_tutorial.py'] + remaining
        tutorial_main()
        return 0
    
    return None


def get_files_to_check(keywords: Optional[str]) -> List[Path]:
    """
    Get list of Python files to check based on keywords.
    
    Args:
        keywords: Optional keyword filter
        
    Returns:
        list: List of Path objects for files to check
    """
    from storm_checker.logic.utils import find_python_files
    
    return find_python_files(
        keywords=keywords,
        exclude_dirs=None,  # Use defaults
    )