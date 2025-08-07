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
    from storm_checker.cli.colors import (
        ColorPrinter, print_header, print_success, print_error,
        print_warning, print_info, print_learn,
        RESET, DIM
    )
    from storm_checker.logic.utils import (
        find_python_files,
        get_project_type
    )
    from storm_checker.logic.mypy_runner import MypyRunner, MypyResult
    from storm_checker.logic.mypy_error_analyzer import ErrorAnalyzer, AnalysisResult
    from storm_checker.logic.progress_tracker import ProgressTracker
except ImportError:
    # For development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from storm_checker.cli.colors import (
        ColorPrinter, print_header, print_success, print_error,
        print_warning, print_info, print_learn,
        RESET, DIM
    )
    from storm_checker.logic.utils import (
        find_python_files,
        get_project_type
    )
    from storm_checker.logic.mypy_runner import MypyRunner, MypyResult
    from storm_checker.logic.mypy_error_analyzer import ErrorAnalyzer, AnalysisResult
    from storm_checker.logic.progress_tracker import ProgressTracker


def print_storm_header(educational: bool = False) -> None:
    """Print Storm-Checker branded header."""
    if educational:
        print_header("Storm-Checker Type Safety Tool", "Learn Python typing through practice")
    else:
        print_header("Storm-Checker Type Safety Tool")


def print_results_standard(
    result: MypyResult,
    analysis: AnalysisResult,
    config_errors: list,
    ignored_count: int = 0,
) -> None:
    """Print streamlined results for experienced developers."""
    if result.total_issues == 0:
        if ignored_count > 0:
            print_success(f"All {result.files_checked} files are type-safe!")
            print_info(f"Note: {ignored_count} warnings intentionally ignored")
        else:
            print_success(f"Perfect! All {result.files_checked} files are type-safe!")
        return

    ignore_note = f" ({ignored_count} intentionally ignored)" if ignored_count > 0 else ""
    print_warning(
        f"Found {result.total_issues} type issues in {result.files_checked} files{ignore_note}"
    )

    # Configuration errors
    if config_errors:
        print(f"\n{ColorPrinter.error('Configuration Issues (Fix these first!)')}")
        for error in config_errors[:2]:
            print(f"  • {error.message}")
        print()

    # Show categories (without tutorial suggestions)
    analyzer = ErrorAnalyzer()
    for category in sorted(analyzer.CATEGORIES, key=lambda c: c.difficulty):
        if category.id in analysis.by_category:
            errors = analysis.by_category[category.id]
            count = len(errors)

            # Color based on difficulty
            if category.difficulty <= 2:
                category_color = "success"
            elif category.difficulty <= 3:
                category_color = "warning"
            else:
                category_color = "error"

            # Print category without tutorial
            print(f"{getattr(ColorPrinter, category_color)(category.name)} "
                  f"(Level {category.difficulty}/5 - {count} issues)")

            # Show first 2 errors
            for error in errors[:2]:
                if ":" in str(error):
                    parts = str(error).split(":", 4)
                    if len(parts) >= 4:
                        file_line = ColorPrinter.info(f"{parts[0]}:{parts[1]}")
                        error_msg = ":".join(parts[2:])
                        print(f"     {file_line}:{error_msg}")

            if count > 2:
                print(f"     {DIM}... and {count - 2} more{RESET}")
            print()

    # Show uncategorized errors (Level 5)
    if "uncategorized" in analysis.by_category:
        errors = analysis.by_category["uncategorized"]
        count = len(errors)

        print(f"{ColorPrinter.error('Complex/Uncategorized Issues')} "
              f"(Level 5/5 - {count} issues)")

        # Show first 2 errors
        for error in errors[:2]:
            if ":" in str(error):
                parts = str(error).split(":", 4)
                if len(parts) >= 4:
                    file_line = ColorPrinter.info(f"{parts[0]}:{parts[1]}")
                    error_msg = ":".join(parts[2:])
                    print(f"     {file_line}:{error_msg}")

        if count > 2:
            print(f"     {DIM}... and {count - 2} more{RESET}")
        print()

    # Show one random fix suggestion
    if analysis.learning_path:
        import random
        error = random.choice(analysis.learning_path[:10])  # Pick from easier errors
        analyzer = ErrorAnalyzer()

        # Find category and difficulty
        category = None
        for cat in analyzer.CATEGORIES:
            if cat.matches_error(error):
                category = cat
                break

        difficulty = category.difficulty if category else 3
        complexity = "Low" if difficulty <= 2 else "Medium" if difficulty <= 3 else "High"

        print(f"\n{ColorPrinter.primary('🎲 Random Fix', bold=True)} (Level {difficulty}, Complexity: {complexity})")
        print(f"{ColorPrinter.info(f'{error.file_path}:{error.line_number}')} - {error.message}")

        # Try to get explanation
        explanation = analyzer.get_explanation(error)
        if explanation and explanation.how_to_fix:
            print(f"Fix: {explanation.how_to_fix[0]}")
        print()


def print_results_educational(
    result: MypyResult,
    analysis: AnalysisResult,
    config_errors: list,
    ignored_count: int = 0,
) -> None:
    """Print formatted results with educational categorization."""
    if result.total_issues == 0:
        if ignored_count > 0:
            print_success(f"All {result.files_checked} files are type-safe!")
            print_info(f"Note: {ignored_count} warnings intentionally ignored")
            print_learn("Your code demonstrates excellent type safety! 🚀")
        else:
            print_success(f"Perfect! All {result.files_checked} files are type-safe!")
            print_learn("You've mastered type annotations! Consider helping others learn.")
        return

    ignore_note = f" ({ignored_count} intentionally ignored)" if ignored_count > 0 else ""
    print_warning(
        f"Found {result.total_issues} type issues in {result.files_checked} files{ignore_note}"
    )

    # Configuration errors are passed separately now
    if config_errors:
        print(f"\n{ColorPrinter.error('⚠️  Configuration Issues (Fix these first!)', bold=True)} "
              f"→ {ColorPrinter.warning('stormcheck tutorial pyproject_setup')}")
        print(f"{ColorPrinter.info('Missing pyproject.toml or MyPy configuration issues detected.')}")
        for error in config_errors[:2]:
            print(f"  • {error.message}")
        print()

    # Show error breakdown by educational category
    print(f"\n{ColorPrinter.learn('📚 Learning Opportunities:', bold=True)}\n")

    # Show categories sorted by difficulty (easiest first)
    analyzer = ErrorAnalyzer()
    for category in sorted(analyzer.CATEGORIES, key=lambda c: c.difficulty):
        if category.id in analysis.by_category:
            errors = analysis.by_category[category.id]
            count = len(errors)

            # Color based on difficulty
            if category.difficulty <= 2:
                category_color = "success"
            elif category.difficulty <= 3:
                category_color = "warning"
            else:
                category_color = "error"

            # Print category with inline tutorial suggestion
            print(f"{getattr(ColorPrinter, category_color)(category.name)} "
                  f"(Level {category.difficulty}/5 - {count} issues) "
                  f"→ {ColorPrinter.warning(f'stormcheck tutorial {category.tutorial_id}')}")

            # Show first 2 errors as examples
            for error in errors[:2]:
                if ":" in str(error):
                    parts = str(error).split(":", 4)
                    if len(parts) >= 4:
                        file_line = ColorPrinter.info(f"{parts[0]}:{parts[1]}")
                        error_msg = ":".join(parts[2:])
                        print(f"     {file_line}:{error_msg}")

            if count > 2:
                print(f"     {DIM}... and {count - 2} more{RESET}")
            print()


def suggest_tutorials(analysis: AnalysisResult) -> None:
    """Suggest tutorials based on the errors found."""
    if not analysis.suggested_tutorials:
        return

    print(f"\n{ColorPrinter.learn('🎓 Recommended Tutorials:', bold=True)}\n")

    for i, tutorial_id in enumerate(analysis.suggested_tutorials[:3], 1):
        print(f"{i}. {ColorPrinter.primary('stormcheck tutorial')} {tutorial_id}")

    if len(analysis.suggested_tutorials) > 3:
        print(f"\n{DIM}Plus {len(analysis.suggested_tutorials) - 3} more tutorials available{RESET}")


def print_learning_path(analysis: AnalysisResult) -> None:
    """Print a suggested learning path through the errors."""
    if not analysis.learning_path:
        return

    print(f"\n{ColorPrinter.learn('🗺️ Suggested Learning Path:', bold=True)}\n")
    print("Fix errors in this order for the best learning experience:\n")

    analyzer = ErrorAnalyzer()
    for i, error in enumerate(analysis.learning_path[:5], 1):
        explanation = analyzer.get_explanation(error)

        print(f"{i}. {ColorPrinter.info(f'{error.file_path}:{error.line_number}')}")
        print(f"   Error: {error.message}")

        if explanation:
            print(f"   {ColorPrinter.success('💡 Quick fix:')} {explanation.simple_explanation}")

        print()


def show_random_issue(result: MypyResult) -> None:
    """Show a random issue to work on."""
    if not result.errors:
        print_success("No errors to show - you've achieved type safety!")
        return

    import random
    error = random.choice(result.errors)
    analyzer = ErrorAnalyzer()

    print(f"\n{ColorPrinter.primary('🎲 Random Issue to Fix:', bold=True)}\n")
    print(f"File: {ColorPrinter.info(f'{error.file_path}:{error.line_number}')}")
    print(f"Error: {error.message}")

    explanation = analyzer.get_explanation(error)
    if explanation:
        print(f"\n{ColorPrinter.success('💡 Explanation:')}")
        print(f"  {explanation.simple_explanation}")
        print(f"\n{ColorPrinter.success('🔧 How to fix:')}")
        for step in explanation.how_to_fix[:3]:
            print(f"  • {step}")

        if explanation.examples:
            print(f"\n{ColorPrinter.success('📝 Example:')}")
            if "before" in explanation.examples:
                print(f"  Before: {explanation.examples['before']}")
            if "after" in explanation.examples:
                print(f"  After: {explanation.examples['after']}")


def print_dashboard(
    result: MypyResult,
    analysis: AnalysisResult,
    tracker: ProgressTracker,
) -> None:
    """Print comprehensive progress dashboard."""
    print_header("Storm-Checker Progress Dashboard", "Track your type safety journey")

    # Get stats
    stats = tracker.get_stats_summary()

    # Progress Overview
    print(f"\n{ColorPrinter.primary('📊 Progress Overview', bold=True)}")
    print(f"├─ Total Fixes: {stats['total_fixes']}")
    print(f"├─ Sessions: {stats['total_sessions']}")
    print(f"├─ Time Invested: {stats['total_time']}")
    print(f"├─ Current Streak: {stats['current_streak']} days")
    print(f"├─ Files Mastered: {stats['files_mastered']}")
    print(f"└─ Velocity: {stats['velocity']:.1f} fixes/day")

    # Learning Progress
    print(f"\n{ColorPrinter.learn('🎓 Learning Progress', bold=True)}")
    print(f"├─ Tutorials Completed: {stats['tutorials_completed']}")
    print(f"├─ Error Types Learned: {stats['unique_error_types']}")
    print(f"└─ Achievements Earned: {stats['achievements_earned']}")

    # Current Status
    print(f"\n{ColorPrinter.primary('📈 Current Analysis', bold=True)}")
    print(f"├─ Complexity Score: {analysis.complexity_score:.1f}/100")
    print(f"├─ Total Issues: {analysis.total_errors}")

    # Show breakdown by difficulty
    for difficulty in range(1, 6):
        if difficulty in analysis.by_difficulty:
            count = len(analysis.by_difficulty[difficulty])
            stars = "⭐" * difficulty
            print(f"├─ Level {difficulty} {stars}: {count} issues")

    print(f"└─ Project Type: {get_project_type()}")

    # Recent Achievements
    achievements = tracker.get_achievements()
    earned = [a for a in achievements if a.is_earned()]
    if earned:
        print(f"\n{ColorPrinter.success('🏆 Recent Achievements', bold=True)}")
        for achievement in earned[-3:]:
            print(f"├─ {achievement.icon} {achievement.name}")

    # Next Steps
    if analysis.suggested_tutorials:
        print(f"\n{ColorPrinter.primary('🎯 Next Steps', bold=True)}")
        print(f"1. Complete tutorial: stormcheck tutorial {analysis.suggested_tutorials[0]}")
        print(f"2. Fix {len(analysis.learning_path[:5])} easy issues to build momentum")
        print(f"3. Check progress: stormcheck mypy --dashboard")


def print_next_steps_standard(
    result: MypyResult,
    analysis: AnalysisResult,
    keywords: Optional[str] = None,
) -> None:
    """Print minimal next steps for standard mode."""
    print(f"\n{ColorPrinter.info('💡 Tips:')}")
    if keywords:
        print(f"• Use -k to check all files")
    else:
        print(f"• Use -k to focus on specific modules")
    print(f"• Track progress with --dashboard")
    print(f"• CI/CD-friendly results with --json")
    print(f"\n{ColorPrinter.learn('📚 Use --edu flag for educational mode with tutorials')}")


def print_next_steps_educational(
    result: MypyResult,
    analysis: AnalysisResult,
    keywords: Optional[str] = None,
) -> None:
    """Print actionable next steps for educational mode."""
    print(f"\n{ColorPrinter.primary('🎯 Next Steps:', bold=True)}\n")

    if result.has_errors:
        # Suggest tutorials first
        if analysis.suggested_tutorials:
            print(f"1. {ColorPrinter.learn('Learn the concepts:')}")
            print(f"   stormcheck tutorial {analysis.suggested_tutorials[0]}")
            print()

        # Suggest easy fixes
        easy_errors = [e for e in analysis.learning_path
                      if any(cat.difficulty <= 2 and cat.matches_error(e)
                            for cat in ErrorAnalyzer().CATEGORIES)]
        if easy_errors:
            print(f"2. {ColorPrinter.success('Start with easy fixes:')}")
            print(f"   {len(easy_errors)} simple issues that take < 5 minutes each")
            print()

        # Run tests
        print(f"3. {ColorPrinter.info('Verify your fixes:')}")
        print(f"   python -m pytest  # Run your test suite")
        print(f"   stormcheck mypy   # Re-check types")

    else:
        print(f"1. {ColorPrinter.success('Celebrate your achievement! 🎉')}")
        print(f"   You've achieved type safety!")
        print()
        print(f"2. {ColorPrinter.learn('Share your knowledge:')}")
        print(f"   Help others learn: stormcheck mypy tutorial --create [COMING SOON]")
        print()
        print(f"3. {ColorPrinter.primary('Level up:')}")
        print(f"   Enable stricter settings in pyproject.toml")

    # Tips
    print(f"\n{ColorPrinter.info('💡 Tips:')}")
    if keywords:
        print(f"• Run without -k to check all files")
    else:
        print(f"• Use -k to focus on specific modules")
    print(f"• Track progress with --dashboard")
    print(f"• CI/CD-friendly results with --json")


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

    # Handle tutorial subcommand
    if args.subcommand == 'tutorial':
        from scripts.mypy_tutorial import main as tutorial_main
        # Restore the remaining args for tutorial parser
        sys.argv = ['mypy_tutorial.py'] + remaining
        tutorial_main()
        return

    # Parse remaining args for main mypy functionality
    args = parser.parse_args()

    # Initialize components
    runner = MypyRunner()
    analyzer = ErrorAnalyzer()
    tracker = ProgressTracker()

    # Print header unless in JSON mode
    if not args.json:
        print_storm_header(educational=args.edu)

    # Check for pyproject.toml
    pyproject_exists = Path("pyproject.toml").exists()

    # Check for pretty=true setting in pyproject.toml
    if pyproject_exists:
        try:
            with open("pyproject.toml", "r") as f:
                content = f.read()
                if "pretty = true" in content or "pretty=true" in content:
                    if not args.json:
                        print_warning("⚠️  PRETTY=TRUE DETECTED! MUST BE FALSE FOR TOOL TO FUNCTION PROPERLY")
                        print_info("Set 'pretty = false' in [tool.mypy] section of pyproject.toml")
                        print()
                    # TODO: Implement multi-line error parsing to support pretty=true
                    # This would require updating MypyRunner.parse_mypy_output() to handle
                    # multi-line error messages where the error code appears on a separate line
        except Exception:
            pass  # Ignore parsing errors

    # Find files
    files = find_python_files(
        keywords=args.keywords,
        exclude_dirs=None,  # Use defaults
    )

    if not args.json:
        if args.keywords:
            print(f"🔎 Searching for: {ColorPrinter.primary(args.keywords)}")
        print(f"📁 Found {ColorPrinter.info(str(len(files)))} Python files\n")

    # Start tracking session
    if not args.no_track:
        tracker.start_session()

    # Run MyPy
    result = runner.run_mypy(files)

    # Check for errors
    if result.return_code == -1:
        print_error("MyPy execution failed!")
        print_info("Check your MyPy installation: pip install mypy")
        sys.exit(1)

    # Add configuration warning if no pyproject.toml
    if not pyproject_exists and not args.json:
        from logic.mypy_runner import MypyError
        config_error = MypyError(
            file_path="<configuration>",
            line_number=0,
            column=None,
            severity="error",
            error_code="config-error",
            message="No pyproject.toml found. Create one for better MyPy configuration and type checking control.",
            raw_line="Missing pyproject.toml"
        )
        result.errors.insert(0, config_error)

    # Filter ignored errors
    genuine_errors, ignored_errors = runner.filter_ignored_errors(result.errors)
    result.errors = genuine_errors

    # Separate configuration errors from regular errors for display
    config_errors = [e for e in result.errors if e.file_path == "<configuration>"]
    regular_errors = [e for e in result.errors if e.file_path != "<configuration>"]

    # Create a modified result for analysis (without config errors)
    analysis_result = MypyResult(
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

    # Analyze errors (excluding config errors which are handled separately)
    analysis = analyzer.analyze_errors(analysis_result)

    # Update tracking
    if not args.no_track:
        # Record error types encountered for learning tracking
        error_codes = set()
        for error in result.errors:
            if error.error_code:
                error_codes.add(error.error_code)

        # Track learned error types (those encountered in this session)
        for error_code in error_codes:
            tracker.record_error_type_encountered(error_code)

        # Record fixes (compare with previous session)
        # TODO: Implement proper fix tracking

        # End session
        tracker.end_session(result)

        # Mark mastered files
        for file_path in files:
            file_errors = [e for e in result.errors if e.file_path == str(file_path)]
            if not file_errors:
                tracker.mark_file_mastered(str(file_path))

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
        import json
        output = {
            "files_checked": result.files_checked,
            "total_issues": result.total_issues,
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "ignored": len(ignored_errors),
            "complexity_score": analysis.complexity_score,
            "categories": {k: len(v) for k, v in analysis.by_category.items()},
            "suggested_tutorials": analysis.suggested_tutorials[:3],
        }
        print(json.dumps(output, indent=2))
        sys.exit(0 if not result.has_errors else 1)

    # Standard output
    if args.edu:
        print_results_educational(result, analysis, config_errors, len(ignored_errors))
    else:
        print_results_standard(result, analysis, config_errors, len(ignored_errors))

    # Educational elements - removed to simplify output
    # The tutorial suggestions are now inline with each error category

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
