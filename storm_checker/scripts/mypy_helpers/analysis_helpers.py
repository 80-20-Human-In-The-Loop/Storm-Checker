#!/usr/bin/env python3
"""
Analysis Helper Functions for Storm-Checker
===========================================
Functions for analyzing and providing learning guidance for type errors.
"""

import random
from typing import Optional
from storm_checker.cli.colors import ColorPrinter, print_success, DIM, RESET
from storm_checker.logic.mypy_runner import MypyResult
from storm_checker.logic.mypy_error_analyzer import ErrorAnalyzer, AnalysisResult


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


def get_error_complexity(error, analyzer: Optional[ErrorAnalyzer] = None) -> tuple:
    """
    Get the difficulty and complexity of an error.
    
    Returns:
        tuple: (difficulty: int, complexity: str, category: ErrorCategory or None)
    """
    if analyzer is None:
        analyzer = ErrorAnalyzer()
    
    category = None
    for cat in analyzer.CATEGORIES:
        if cat.matches_error(error):
            category = cat
            break
    
    difficulty = category.difficulty if category else 3
    complexity = "Low" if difficulty <= 2 else "Medium" if difficulty <= 3 else "High"
    
    return difficulty, complexity, category


def categorize_errors_by_difficulty(analysis: AnalysisResult) -> dict:
    """
    Categorize errors by their difficulty level.
    
    Returns:
        dict: Mapping of difficulty level (1-5) to list of errors
    """
    categorized = {}
    for difficulty in range(1, 6):
        if difficulty in analysis.by_difficulty:
            categorized[difficulty] = analysis.by_difficulty[difficulty]
    return categorized


def get_quick_wins(analysis: AnalysisResult, max_items: int = 5) -> list:
    """
    Get a list of quick wins - easy errors that can be fixed quickly.
    
    Args:
        analysis: The analysis result
        max_items: Maximum number of quick wins to return
        
    Returns:
        list: List of easy-to-fix errors
    """
    analyzer = ErrorAnalyzer()
    easy_errors = []
    
    for error in analysis.learning_path:
        difficulty, _, _ = get_error_complexity(error, analyzer)
        if difficulty <= 2:
            easy_errors.append(error)
            if len(easy_errors) >= max_items:
                break
    
    return easy_errors


def calculate_learning_progress(analysis: AnalysisResult) -> dict:
    """
    Calculate learning progress metrics from the analysis.
    
    Returns:
        dict: Dictionary containing progress metrics
    """
    total_errors = analysis.total_errors
    
    # Count errors by difficulty
    easy_errors = len(analysis.by_difficulty.get(1, [])) + len(analysis.by_difficulty.get(2, []))
    medium_errors = len(analysis.by_difficulty.get(3, []))
    hard_errors = len(analysis.by_difficulty.get(4, [])) + len(analysis.by_difficulty.get(5, []))
    
    # Calculate percentages
    easy_pct = (easy_errors / total_errors * 100) if total_errors > 0 else 0
    medium_pct = (medium_errors / total_errors * 100) if total_errors > 0 else 0
    hard_pct = (hard_errors / total_errors * 100) if total_errors > 0 else 0
    
    # Estimate time to fix (rough estimates)
    time_estimate = (easy_errors * 2 + medium_errors * 5 + hard_errors * 10)  # minutes
    
    return {
        'total_errors': total_errors,
        'easy_errors': easy_errors,
        'medium_errors': medium_errors,
        'hard_errors': hard_errors,
        'easy_percentage': easy_pct,
        'medium_percentage': medium_pct,
        'hard_percentage': hard_pct,
        'complexity_score': analysis.complexity_score,
        'estimated_time_minutes': time_estimate,
        'unique_categories': len(analysis.by_category),
        'suggested_tutorials': len(analysis.suggested_tutorials),
    }