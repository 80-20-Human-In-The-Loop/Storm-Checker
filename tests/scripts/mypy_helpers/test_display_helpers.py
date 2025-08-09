"""
Comprehensive Tests for Display Helpers
========================================
Complete test coverage for display helper functions.
"""

import pytest
import random
import sys
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from storm_checker.scripts.mypy_helpers.display_helpers import (
    print_storm_header, print_results_standard, print_results_educational,
    print_dashboard, print_next_steps_standard, print_next_steps_educational
)
from storm_checker.logic.mypy_runner import MypyResult, MypyError
from storm_checker.logic.mypy_error_analyzer import AnalysisResult, ErrorCategory
from storm_checker.logic.progress_tracker import ProgressTracker


def create_mock_error(
    file_path="test.py",
    line_number=10,
    severity="error",
    message="Type error",
    error_code="type-error"
):
    """Helper to create mock MypyError."""
    error = Mock(spec=MypyError)
    error.file_path = file_path
    error.line_number = line_number
    error.severity = severity
    error.message = message
    error.error_code = error_code
    error.__str__ = Mock(return_value=f"{file_path}:{line_number}: {severity}: {message}")
    return error


def create_mock_result(total_issues=0, files_checked=10, errors=None):
    """Helper to create mock MypyResult."""
    result = Mock(spec=MypyResult)
    result.total_issues = total_issues
    result.files_checked = files_checked
    result.errors = errors or []
    result.warnings = []
    result.notes = []
    result.has_errors = total_issues > 0
    return result


def create_mock_analysis(
    total_errors=0,
    complexity_score=50.0,
    by_category=None,
    by_difficulty=None,
    suggested_tutorials=None,
    learning_path=None
):
    """Helper to create mock AnalysisResult."""
    analysis = Mock(spec=AnalysisResult)
    analysis.total_errors = total_errors
    analysis.complexity_score = complexity_score
    analysis.by_category = by_category or {}
    analysis.by_difficulty = by_difficulty or {}
    analysis.suggested_tutorials = suggested_tutorials or []
    analysis.learning_path = learning_path or []
    return analysis


class TestPrintStormHeader:
    """Test print_storm_header function."""
    
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_header')
    def test_print_storm_header_standard(self, mock_print_header):
        """Test standard header printing."""
        print_storm_header(educational=False)
        mock_print_header.assert_called_once_with("Storm-Checker Type Safety Tool")
    
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_header')
    def test_print_storm_header_educational(self, mock_print_header):
        """Test educational header printing."""
        print_storm_header(educational=True)
        mock_print_header.assert_called_once_with(
            "Storm-Checker Type Safety Tool",
            "Learn Python typing through practice"
        )


class TestPrintResultsStandard:
    """Test print_results_standard function."""
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_success')
    def test_print_results_standard_no_issues(self, mock_success, mock_print):
        """Test with no type issues."""
        result = create_mock_result(total_issues=0, files_checked=5)
        analysis = create_mock_analysis()
        
        print_results_standard(result, analysis, [], ignored_count=0)
        
        mock_success.assert_called_once_with("Perfect! All 5 files are type-safe!")
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_info')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_success')
    def test_print_results_standard_no_issues_with_ignored(self, mock_success, mock_info, mock_print):
        """Test with no issues but some ignored warnings."""
        result = create_mock_result(total_issues=0, files_checked=5)
        analysis = create_mock_analysis()
        
        print_results_standard(result, analysis, [], ignored_count=3)
        
        mock_success.assert_called_once_with("All 5 files are type-safe!")
        mock_info.assert_called_once_with("Note: 3 warnings intentionally ignored")
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_warning')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ErrorAnalyzer')
    def test_print_results_standard_with_issues(self, mock_analyzer_class, mock_warning, mock_print):
        """Test with type issues."""
        # Create mock categories
        cat1 = Mock()
        cat1.id = "basic"
        cat1.name = "Basic Type Errors"
        cat1.difficulty = 1
        cat1.tutorial_id = "basic_types"
        
        cat2 = Mock()
        cat2.id = "advanced"
        cat2.name = "Advanced Issues"
        cat2.difficulty = 4
        cat2.tutorial_id = "advanced"
        
        mock_analyzer = Mock()
        mock_analyzer.CATEGORIES = [cat1, cat2]
        mock_analyzer.get_explanation.return_value = Mock(how_to_fix=["Fix this way"])
        mock_analyzer_class.return_value = mock_analyzer
        
        # Create errors
        error1 = create_mock_error(message="Basic error")
        error2 = create_mock_error(message="Advanced error", line_number=20)
        
        result = create_mock_result(total_issues=2, files_checked=5, errors=[error1, error2])
        analysis = create_mock_analysis(
            total_errors=2,
            by_category={"basic": [error1], "advanced": [error2]},
            learning_path=[error1, error2]
        )
        
        # Mock random.choice to return error1
        with patch('random.choice', return_value=error1):
            print_results_standard(result, analysis, [], ignored_count=0)
        
        mock_warning.assert_called_once_with("Found 2 type issues in 5 files")
        # Check that categories were printed
        assert mock_print.called
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ColorPrinter')
    def test_print_results_standard_with_config_errors(self, mock_color_printer, mock_print):
        """Test with configuration errors."""
        config_error = create_mock_error(
            file_path="<configuration>",
            message="Missing pyproject.toml"
        )
        
        result = create_mock_result(total_issues=1, files_checked=5)
        analysis = create_mock_analysis(total_errors=1)
        
        print_results_standard(result, analysis, [config_error], ignored_count=0)
        
        # Check that config error was displayed
        mock_color_printer.error.assert_called()
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ErrorAnalyzer')
    def test_print_results_standard_uncategorized(self, mock_analyzer_class, mock_print):
        """Test with uncategorized errors."""
        mock_analyzer = Mock()
        mock_analyzer.CATEGORIES = []
        mock_analyzer_class.return_value = mock_analyzer
        
        error = create_mock_error(message="Uncategorized error")
        
        result = create_mock_result(total_issues=1, files_checked=5, errors=[error])
        analysis = create_mock_analysis(
            total_errors=1,
            by_category={"uncategorized": [error]}
        )
        
        print_results_standard(result, analysis, [], ignored_count=0)
        
        # Check that uncategorized section was printed
        assert mock_print.called
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ErrorAnalyzer')
    def test_print_results_standard_many_errors(self, mock_analyzer_class, mock_print):
        """Test with many errors (should show ellipsis)."""
        cat = Mock()
        cat.id = "many"
        cat.name = "Many Errors"
        cat.difficulty = 2
        
        mock_analyzer = Mock()
        mock_analyzer.CATEGORIES = [cat]
        mock_analyzer_class.return_value = mock_analyzer
        
        # Create many errors
        errors = [create_mock_error(line_number=i) for i in range(10)]
        
        result = create_mock_result(total_issues=10, files_checked=5, errors=errors)
        analysis = create_mock_analysis(
            total_errors=10,
            by_category={"many": errors}
        )
        
        print_results_standard(result, analysis, [], ignored_count=0)
        
        # Check that ellipsis was shown for remaining errors
        print_calls = str(mock_print.call_args_list)
        assert "... and 8 more" in print_calls


class TestPrintResultsEducational:
    """Test print_results_educational function."""
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_learn')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_success')
    def test_print_results_educational_perfect(self, mock_success, mock_learn, mock_print):
        """Test perfect score in educational mode."""
        result = create_mock_result(total_issues=0, files_checked=5)
        analysis = create_mock_analysis()
        
        print_results_educational(result, analysis, [], ignored_count=0)
        
        mock_success.assert_called_once_with("Perfect! All 5 files are type-safe!")
        mock_learn.assert_called_once_with(
            "You've mastered type annotations! Consider helping others learn."
        )
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_learn')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_info')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_success')
    def test_print_results_educational_perfect_with_ignored(
        self, mock_success, mock_info, mock_learn, mock_print
    ):
        """Test perfect score with ignored warnings."""
        result = create_mock_result(total_issues=0, files_checked=5)
        analysis = create_mock_analysis()
        
        print_results_educational(result, analysis, [], ignored_count=2)
        
        mock_success.assert_called_once_with("All 5 files are type-safe!")
        mock_info.assert_called_once_with("Note: 2 warnings intentionally ignored")
        mock_learn.assert_called_once_with("Your code demonstrates excellent type safety! 🚀")
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ColorPrinter')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ErrorAnalyzer')
    def test_print_results_educational_with_errors(
        self, mock_analyzer_class, mock_color_printer, mock_print
    ):
        """Test educational mode with errors."""
        # Setup mock category
        cat = Mock()
        cat.id = "basic"
        cat.name = "Basic Issues"
        cat.difficulty = 1
        cat.tutorial_id = "basic_tutorial"
        
        mock_analyzer = Mock()
        mock_analyzer.CATEGORIES = [cat]
        mock_analyzer_class.return_value = mock_analyzer
        
        error = create_mock_error()
        result = create_mock_result(total_issues=1, files_checked=5, errors=[error])
        analysis = create_mock_analysis(
            total_errors=1,
            by_category={"basic": [error]}
        )
        
        print_results_educational(result, analysis, [], ignored_count=0)
        
        # Check that learning opportunities were shown
        mock_color_printer.learn.assert_called()
        assert mock_print.called
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ColorPrinter')
    def test_print_results_educational_with_config_errors(self, mock_color_printer, mock_print):
        """Test educational mode with configuration errors."""
        config_error = create_mock_error(
            file_path="<configuration>",
            message="Configuration issue"
        )
        
        result = create_mock_result(total_issues=1, files_checked=5)
        analysis = create_mock_analysis(total_errors=1)
        
        print_results_educational(result, analysis, [config_error], ignored_count=0)
        
        # Check that config issues were highlighted
        assert mock_color_printer.error.called
        assert mock_color_printer.warning.called  # Tutorial suggestion


class TestPrintDashboard:
    """Test print_dashboard function."""
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_header')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.get_project_type')
    def test_print_dashboard_v2_api(self, mock_project_type, mock_header, mock_print):
        """Test dashboard with v2 API tracker."""
        mock_project_type.return_value = "django"
        
        tracker = Mock()
        tracker.get_dashboard_data = Mock(return_value={
            'overall_stats': {
                'files_analyzed': 100,
                'errors_fixed': 50,
                'type_coverage': {'current': 85.5},
                'current_streak': 5,
                'time_saved': 2.5
            },
            'tutorial_progress': {
                'completed': 7,
                'total': 10,
                'average_score': 88.5
            },
            'achievements': {
                'unlocked': 12,
                'total': 20
            }
        })
        # Mock get_achievements to return an empty list
        tracker.get_achievements = Mock(return_value=[])
        
        result = create_mock_result()
        analysis = create_mock_analysis(
            complexity_score=65.0,
            total_errors=10,
            by_difficulty={1: [Mock()] * 3, 2: [Mock()] * 5, 3: [Mock()] * 2}
        )
        
        print_dashboard(result, analysis, tracker)
        
        mock_header.assert_called_once()
        # Check that stats were printed
        print_calls = str(mock_print.call_args_list)
        assert "Files Analyzed: 100" in print_calls
        assert "Errors Fixed: 50" in print_calls
        assert "Type Coverage: 85.5%" in print_calls
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_header')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.get_project_type')
    def test_print_dashboard_v1_api(self, mock_project_type, mock_header, mock_print):
        """Test dashboard with v1 API tracker."""
        mock_project_type.return_value = "flask"
        
        # Create v1 tracker
        tracker = Mock()
        tracker.get_stats_summary = Mock(return_value={
            'total_fixes': 30,
            'total_sessions': 10,
            'total_time': '5h 30m',
            'current_streak': 3,
            'files_mastered': 15,
            'velocity': 2.5,
            'tutorials_completed': 5,
            'unique_error_types': 12,
            'achievements_earned': 8
        })
        # Mock get_achievements to return an empty list
        tracker.get_achievements = Mock(return_value=[])
        
        result = create_mock_result()
        analysis = create_mock_analysis(
            complexity_score=45.0,
            total_errors=5,
            by_difficulty={1: [Mock()] * 5}
        )
        
        # Mock hasattr to return False only for get_dashboard_data
        original_hasattr = hasattr
        def mock_hasattr(obj, attr):
            if attr == 'get_dashboard_data':
                return False
            return original_hasattr(obj, attr)
        
        with patch('builtins.hasattr', side_effect=mock_hasattr):
            print_dashboard(result, analysis, tracker)
        
        # Check v1 stats were printed
        print_calls = str(mock_print.call_args_list)
        assert "Total Fixes: 30" in print_calls
        assert "Sessions: 10" in print_calls
        assert "Velocity: 2.5 fixes/day" in print_calls
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_header')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.get_project_type')
    def test_print_dashboard_with_achievements(self, mock_project_type, mock_header, mock_print):
        """Test dashboard with achievements."""
        mock_project_type.return_value = "package"
        
        # Create mock achievements
        achievement1 = Mock()
        achievement1.icon = "🏆"
        achievement1.name = "First Fix"
        achievement1.is_earned.return_value = True
        
        achievement2 = Mock()
        achievement2.icon = "⭐"
        achievement2.name = "Type Master"
        achievement2.is_earned.return_value = True
        
        achievement3 = Mock()
        achievement3.is_earned.return_value = False
        
        tracker = Mock()
        tracker.get_dashboard_data = Mock(return_value={
            'overall_stats': {
                'files_analyzed': 20,
                'errors_fixed': 15,
                'type_coverage': {'current': 75.0},
                'current_streak': 2,
                'time_saved': 1.5
            },
            'tutorial_progress': {
                'completed': 3,
                'total': 10,
                'average_score': 85.0
            },
            'achievements': {
                'unlocked': 2,
                'total': 15
            }
        })
        tracker.get_achievements = Mock(return_value=[achievement1, achievement2, achievement3])
        
        result = create_mock_result()
        analysis = create_mock_analysis()
        
        print_dashboard(result, analysis, tracker)
        
        # Check achievements were shown
        print_calls = str(mock_print.call_args_list)
        assert "First Fix" in print_calls
        assert "Type Master" in print_calls
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.print_header')
    def test_print_dashboard_next_steps(self, mock_header, mock_print):
        """Test dashboard with next steps."""
        tracker = Mock()
        tracker.get_dashboard_data = Mock(return_value={
            'overall_stats': {
                'files_analyzed': 50,
                'errors_fixed': 25,
                'type_coverage': {'current': 80.0},
                'current_streak': 7,
                'time_saved': 3.0
            },
            'tutorial_progress': {
                'completed': 5,
                'total': 10,
                'average_score': 90.0
            },
            'achievements': {
                'unlocked': 8,
                'total': 20
            }
        })
        # Mock get_achievements to return an empty list
        tracker.get_achievements = Mock(return_value=[])
        
        result = create_mock_result()
        analysis = create_mock_analysis(
            suggested_tutorials=["basic_types", "advanced_types"],
            learning_path=[Mock()] * 10
        )
        
        print_dashboard(result, analysis, tracker)
        
        # Check next steps were shown
        print_calls = str(mock_print.call_args_list)
        assert "Next Steps" in print_calls
        assert "basic_types" in print_calls


class TestPrintNextSteps:
    """Test next steps functions."""
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ColorPrinter')
    def test_print_next_steps_standard_with_keywords(self, mock_color_printer, mock_print):
        """Test standard next steps with keywords."""
        result = create_mock_result()
        analysis = create_mock_analysis()
        
        print_next_steps_standard(result, analysis, keywords="models")
        
        # Check tips were printed
        mock_color_printer.info.assert_called()
        print_calls = str(mock_print.call_args_list)
        assert "Use -k to check all files" in print_calls
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ColorPrinter')
    def test_print_next_steps_standard_without_keywords(self, mock_color_printer, mock_print):
        """Test standard next steps without keywords."""
        result = create_mock_result()
        analysis = create_mock_analysis()
        
        print_next_steps_standard(result, analysis, keywords=None)
        
        print_calls = str(mock_print.call_args_list)
        assert "Use -k to focus on specific modules" in print_calls
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ColorPrinter')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ErrorAnalyzer')
    def test_print_next_steps_educational_with_errors(
        self, mock_analyzer_class, mock_color_printer, mock_print
    ):
        """Test educational next steps with errors."""
        # Create mock category
        cat = Mock()
        cat.difficulty = 1
        cat.matches_error = Mock(return_value=True)
        
        mock_analyzer = Mock()
        mock_analyzer.CATEGORIES = [cat]
        mock_analyzer_class.return_value = mock_analyzer
        
        error = create_mock_error()
        result = create_mock_result(total_issues=1, files_checked=5, errors=[error])
        result.has_errors = True
        
        analysis = create_mock_analysis(
            suggested_tutorials=["basic_tutorial"],
            learning_path=[error]
        )
        
        print_next_steps_educational(result, analysis)
        
        # Check educational steps were shown
        mock_color_printer.primary.assert_called()
        mock_color_printer.learn.assert_called()
        print_calls = str(mock_print.call_args_list)
        assert "basic_tutorial" in print_calls
    
    @patch('builtins.print')
    @patch('storm_checker.scripts.mypy_helpers.display_helpers.ColorPrinter')
    def test_print_next_steps_educational_no_errors(self, mock_color_printer, mock_print):
        """Test educational next steps with no errors."""
        result = create_mock_result(total_issues=0, files_checked=5)
        result.has_errors = False
        
        analysis = create_mock_analysis()
        
        # The function should handle the no-error case
        print_next_steps_educational(result, analysis)
        
        # Should still print header
        mock_color_printer.primary.assert_called()


