#!/usr/bin/env python3
"""
Storm-Checker MyPy Type Checker
===============================
An educational type checking tool that helps developers learn about Python's type
system through gamification and progressive learning.

This open-source tool transforms type checking from a chore into a learning journey,
showcasing the importance of static typing in Python development.

Usage:
    python scripts/check_mypy.py                    # Check all Python files
    python scripts/check_mypy.py -k models          # Check files with 'models' in name
    python scripts/check_mypy.py -k "models|views"  # Multiple keywords
    python scripts/check_mypy.py --dashboard        # Show progress dashboard
    python scripts/check_mypy.py --tutorial         # Get tutorial suggestions
    python scripts/check_mypy.py --random           # Get a random issue to fix
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    # When installed via pip
    from storm_checker.cli.colors import ColorPrinter, print_error, print_info
    from storm_checker.logic.mypy_runner import MypyRunner
    from storm_checker.logic.mypy_error_analyzer import ErrorAnalyzer
    from storm_checker.logic.progress_tracker import ProgressTracker
    from storm_checker.scripts.mypy_helpers import (
        # Display helpers
        print_storm_header,
        print_results_standard,
        print_results_educational,
        print_next_steps_standard,
        print_next_steps_educational,
        print_dashboard,
        # Analysis helpers
        suggest_tutorials,
        print_learning_path,
        show_random_issue,
        # Utility helpers
        check_pyproject_config,
        filter_and_categorize_errors,
        setup_tracking_session,
        process_json_output,
        get_file_errors,
    )
    from storm_checker.scripts.mypy_helpers.utility_helpers import (
        warn_about_pretty_true,
        create_config_error,
        end_tracking_session,
        create_analysis_result,
        should_exit_early,
        get_files_to_check,
    )
except ImportError:
    # For development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from storm_checker.cli.colors import ColorPrinter, print_error, print_info
    from storm_checker.logic.mypy_runner import MypyRunner
    from storm_checker.logic.mypy_error_analyzer import ErrorAnalyzer
    from storm_checker.logic.progress_tracker import ProgressTracker
    from storm_checker.scripts.mypy_helpers import (
        # Display helpers
        print_storm_header,
        print_results_standard,
        print_results_educational,
        print_next_steps_standard,
        print_next_steps_educational,
        print_dashboard,
        # Analysis helpers
        suggest_tutorials,
        print_learning_path,
        show_random_issue,
        # Utility helpers
        check_pyproject_config,
        filter_and_categorize_errors,
        setup_tracking_session,
        process_json_output,
        get_file_errors,
    )
    from storm_checker.scripts.mypy_helpers.utility_helpers import (
        warn_about_pretty_true,
        create_config_error,
        end_tracking_session,
        create_analysis_result,
        should_exit_early,
        get_files_to_check,
    )


def main() -> None:
    """Main entry point for Storm-Checker."""
    parser = argparse.ArgumentParser(
        description="Storm-Checker: Learn Python typing through practice",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest='subcommand', help='Available subcommands')

    # Default MyPy checking (no subcommand)
    # Add arguments directly to main parser for backward compatibility
    parser.add_argument(
        "-k", "--keywords",
        help="Keywords to filter files (regex supported)",
        default=None,
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Show comprehensive progress dashboard",
    )
    parser.add_argument(
        "--tutorial",
        action="store_true",
        help="Get tutorial suggestions based on current errors",
    )
    parser.add_argument(
        "--random",
        action="store_true",
        help="Show a random issue to work on",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--no-track",
        action="store_true",
        help="Don't track progress for this session",
    )
    parser.add_argument(
        "--show-ignored",
        action="store_true",
        help="Show intentionally ignored warnings",
    )
    parser.add_argument(
        "--edu",
        action="store_true",
        help="Educational mode with tutorials and learning guidance",
    )

    # Tutorial subcommand
    tutorial_parser = subparsers.add_parser(
        'tutorial',
        help='MyPy-specific tutorials for learning type safety'
    )

    args, remaining = parser.parse_known_args()

    # Check for early exit conditions (tutorial subcommand)
    exit_code = should_exit_early(args)
    if exit_code is not None:
        sys.exit(exit_code)

    # Parse remaining args for main mypy functionality
    args = parser.parse_args()

    # Initialize components
    runner = MypyRunner()
    analyzer = ErrorAnalyzer()
    tracker = ProgressTracker()

    # Print header unless in JSON mode
    if not args.json:
        print_storm_header(educational=args.edu)

    # Check for pyproject.toml and configuration issues
    pyproject_exists, has_pretty_true = check_pyproject_config()
    
    if has_pretty_true:
        warn_about_pretty_true(args.json)

    # Find files to check
    files = get_files_to_check(args.keywords)

    if not args.json:
        if args.keywords:
            print(f"🔎 Searching for: {ColorPrinter.primary(args.keywords)}")
        print(f"📁 Found {ColorPrinter.info(str(len(files)))} Python files\n")

    # Start tracking session
    setup_tracking_session(tracker, args.no_track)

    # Run MyPy
    result = runner.run_mypy(files)

    # Check for errors
    if result.return_code == -1:
        print_error("MyPy execution failed!")
        print_info("Check your MyPy installation: pip install mypy")
        sys.exit(1)

    # Add configuration warning if no pyproject.toml
    if not pyproject_exists and not args.json:
        config_error = create_config_error()
        result.errors.insert(0, config_error)

    # Filter and categorize errors
    genuine_errors, ignored_errors, config_errors, regular_errors = filter_and_categorize_errors(
        result.errors, runner
    )
    result.errors = genuine_errors

    # Create a modified result for analysis (without config errors)
    analysis_result = create_analysis_result(result, config_errors)

    # Analyze errors (excluding config errors which are handled separately)
    analysis = analyzer.analyze_errors(analysis_result)

    # Update tracking
    end_tracking_session(tracker, result, files, args.no_track)

    # Handle special modes
    if args.random:
        show_random_issue(result)
        sys.exit(0 if not result.has_errors else 1)

    if args.dashboard:
        print_dashboard(result, analysis, tracker)
        sys.exit(0 if not result.has_errors else 1)

    if args.tutorial:
        suggest_tutorials(analysis)
        print_learning_path(analysis)
        sys.exit(0 if not result.has_errors else 1)

    # JSON output
    if args.json:
        json_output = process_json_output(result, analysis, len(ignored_errors))
        print(json_output)
        sys.exit(0 if not result.has_errors else 1)

    # Standard output
    if args.edu:
        print_results_educational(result, analysis, config_errors, len(ignored_errors))
    else:
        print_results_standard(result, analysis, config_errors, len(ignored_errors))

    # Next steps
    if args.edu:
        print_next_steps_educational(result, analysis, args.keywords)
    else:
        print_next_steps_standard(result, analysis, args.keywords)

    # Final status with motivational message (only in educational mode)
    if args.edu:
        if not result.has_errors:
            print(f"\n{ColorPrinter.success('🎉 Congratulations!', bold=True)} "
                  f"You've achieved type safety!\n")
        else:
            print(f"\n{ColorPrinter.learn('📚 Keep learning!', bold=True)} "
                  f"You're making great progress.\n")

    # Exit with appropriate code
    sys.exit(0 if not result.has_errors else 1)


if __name__ == "__main__":
    main()