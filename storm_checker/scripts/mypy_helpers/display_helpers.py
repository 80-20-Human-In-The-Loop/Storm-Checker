#!/usr/bin/env python3
"""
Display Helper Functions for Storm-Checker
==========================================
Functions for formatting and displaying type checking results.
"""

from typing import Optional, List
from storm_checker.cli.colors import (
    ColorPrinter, print_header, print_success, print_error,
    print_warning, print_info, print_learn,
    RESET, DIM
)
from storm_checker.logic.mypy_runner import MypyResult, MypyError
from storm_checker.logic.mypy_error_analyzer import ErrorAnalyzer, AnalysisResult
from storm_checker.logic.progress_tracker import ProgressTracker
from storm_checker.logic.utils import get_project_type


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


def print_dashboard(
    result: MypyResult,
    analysis: AnalysisResult,
    tracker: ProgressTracker,
) -> None:
    """Print comprehensive progress dashboard."""
    print_header("Storm-Checker Progress Dashboard", "Track your type safety journey")

    # Get stats - use v2 API if available, otherwise use defaults
    if hasattr(tracker, 'get_dashboard_data'):
        # Use v2 API
        dashboard_data = tracker.get_dashboard_data()
        overall_stats = dashboard_data.get('overall_stats', {})
        tutorial_progress = dashboard_data.get('tutorial_progress', {})
        achievements = dashboard_data.get('achievements', {})
        
        # Progress Overview
        print(f"\n{ColorPrinter.primary('📊 Progress Overview', bold=True)}")
        print(f"├─ Files Analyzed: {overall_stats.get('files_analyzed', 0)}")
        print(f"├─ Errors Fixed: {overall_stats.get('errors_fixed', 0)}")
        print(f"├─ Type Coverage: {overall_stats.get('type_coverage', {}).get('current', 0):.1f}%")
        print(f"├─ Current Streak: {overall_stats.get('current_streak', 0)} days")
        print(f"└─ Time Saved: {overall_stats.get('time_saved', 0):.1f} hours")
        
        # Learning Progress
        print(f"\n{ColorPrinter.learn('🎓 Learning Progress', bold=True)}")
        print(f"├─ Tutorials Completed: {tutorial_progress.get('completed', 0)}/{tutorial_progress.get('total', 10)}")
        print(f"├─ Average Score: {tutorial_progress.get('average_score', 0):.0f}%")
        print(f"└─ Achievements Earned: {achievements.get('unlocked', 0)}/{achievements.get('total', 0)}")
        
    else:
        # Fallback for v1 API or missing methods
        stats = {}
        if hasattr(tracker, 'get_stats_summary'):
            stats = tracker.get_stats_summary()
        
        # Progress Overview
        print(f"\n{ColorPrinter.primary('📊 Progress Overview', bold=True)}")
        print(f"├─ Total Fixes: {stats.get('total_fixes', 0)}")
        print(f"├─ Sessions: {stats.get('total_sessions', 0)}")
        print(f"├─ Time Invested: {stats.get('total_time', 'N/A')}")
        print(f"├─ Current Streak: {stats.get('current_streak', 0)} days")
        print(f"├─ Files Mastered: {stats.get('files_mastered', 0)}")
        print(f"└─ Velocity: {stats.get('velocity', 0):.1f} fixes/day")
        
        # Learning Progress
        print(f"\n{ColorPrinter.learn('🎓 Learning Progress', bold=True)}")
        print(f"├─ Tutorials Completed: {stats.get('tutorials_completed', 0)}")
        print(f"├─ Error Types Learned: {stats.get('unique_error_types', 0)}")
        print(f"└─ Achievements Earned: {stats.get('achievements_earned', 0)}")

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

    # Recent Achievements (if available)
    if hasattr(tracker, 'get_achievements'):
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