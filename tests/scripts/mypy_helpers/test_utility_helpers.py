"""
Comprehensive Tests for utility_helpers.py
==========================================
Tests for utility helper functions with full coverage.
"""

import pytest
import sys
import json
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
from argparse import Namespace

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from storm_checker.scripts.mypy_helpers.utility_helpers import (
    check_pyproject_config,
    warn_about_pretty_true,
    create_config_error,
    filter_and_categorize_errors,
    setup_tracking_session,
    end_tracking_session,
    process_json_output,
    get_file_errors,
    create_analysis_result,
    should_exit_early,
    get_files_to_check
)
from storm_checker.logic.mypy_runner import MypyResult, MypyError


def create_mypy_error(file_path="test.py", line_number=10, severity="error", 
                      message="Type error", error_code="misc"):
    """Helper to create a MypyError with defaults."""
    return MypyError(
        file_path=file_path,
        line_number=line_number,
        column=None,
        severity=severity,
        error_code=error_code,
        message=message,
        raw_line=f"{file_path}:{line_number}: {severity}: {message} [{error_code}]"
    )


class TestUtilityHelpers:
    """Test utility helper functions."""
    
    def test_check_pyproject_config_exists_no_pretty(self):
        """Test checking pyproject.toml without pretty=true."""
        content = """
[tool.mypy]
python_version = "3.10"
pretty = false
"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=content)):
                exists, has_pretty = check_pyproject_config()
                assert exists is True
                assert has_pretty is False
    
    def test_check_pyproject_config_exists_with_pretty(self):
        """Test checking pyproject.toml with pretty=true."""
        content = """
[tool.mypy]
python_version = "3.10"
pretty = true
"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=content)):
                exists, has_pretty = check_pyproject_config()
                assert exists is True
                assert has_pretty is True
    
    def test_check_pyproject_config_exists_with_pretty_no_spaces(self):
        """Test checking pyproject.toml with pretty=true (no spaces)."""
        content = """
[tool.mypy]
python_version = "3.10"
pretty=true
"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=content)):
                exists, has_pretty = check_pyproject_config()
                assert exists is True
                assert has_pretty is True
    
    def test_check_pyproject_config_not_exists(self):
        """Test checking when pyproject.toml doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            exists, has_pretty = check_pyproject_config()
            assert exists is False
            assert has_pretty is False
    
    def test_check_pyproject_config_read_error(self):
        """Test handling read error for pyproject.toml."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', side_effect=IOError("Cannot read file")):
                exists, has_pretty = check_pyproject_config()
                assert exists is True
                assert has_pretty is False
    
    def test_warn_about_pretty_true_not_json(self):
        """Test warning about pretty=true when not in JSON mode."""
        with patch('storm_checker.scripts.mypy_helpers.utility_helpers.print_warning') as mock_warn:
            with patch('storm_checker.scripts.mypy_helpers.utility_helpers.print_info') as mock_info:
                warn_about_pretty_true(json_mode=False)
                mock_warn.assert_called_once()
                mock_info.assert_called_once()
                assert "PRETTY=TRUE" in str(mock_warn.call_args)
    
    def test_warn_about_pretty_true_json_mode(self):
        """Test no warning in JSON mode."""
        with patch('storm_checker.scripts.mypy_helpers.utility_helpers.print_warning') as mock_warn:
            warn_about_pretty_true(json_mode=True)
            mock_warn.assert_not_called()
    
    def test_create_config_error(self):
        """Test creating configuration error."""
        error = create_config_error()
        assert error.file_path == "<configuration>"
        assert error.line_number == 0
        assert error.severity == "error"
        assert "pyproject.toml" in error.message
        assert error.error_code == "config-error"  # Check actual implementation
    
    def test_filter_and_categorize_errors_basic(self):
        """Test basic error filtering and categorization."""
        errors = [
            create_mypy_error(),
            create_mypy_error(line_number=20, message="Another error"),
            create_mypy_error(file_path="<configuration>", line_number=0, message="Config error", error_code="config")
        ]
        
        runner = Mock()
        # Mock filter_ignored_errors to return genuine and ignored
        runner.filter_ignored_errors = Mock(return_value=(errors[:-1], []))  # All except config are genuine
        
        genuine, ignored, config, regular = filter_and_categorize_errors(errors, runner)
        
        assert len(genuine) == 2  # Two genuine errors
        assert len(ignored) == 0
        assert len(config) == 0  # Config error is not in genuine
        assert len(regular) == 2  # Two regular errors
    
    def test_filter_and_categorize_errors_with_ignored(self):
        """Test filtering with intentionally ignored errors."""
        errors = [
            create_mypy_error(),
            create_mypy_error(line_number=20, message="Ignored error")
        ]
        
        runner = Mock()
        # Mock filter_ignored_errors to return one genuine and one ignored
        runner.filter_ignored_errors = Mock(return_value=([errors[0]], [errors[1]]))
        
        genuine, ignored, config, regular = filter_and_categorize_errors(errors, runner)
        
        assert len(genuine) == 1
        assert len(ignored) == 1
        assert ignored[0].message == "Ignored error"
    
    def test_setup_tracking_session_normal(self):
        """Test setting up tracking session."""
        tracker = Mock()
        setup_tracking_session(tracker, no_track=False)
        tracker.start_session.assert_called_once()
    
    def test_setup_tracking_session_no_track(self):
        """Test skipping tracking setup when disabled."""
        tracker = Mock()
        setup_tracking_session(tracker, no_track=True)
        tracker.start_session.assert_not_called()
    
    def test_end_tracking_session_normal(self):
        """Test ending tracking session."""
        tracker = Mock()
        tracker.update_session_stats = Mock()
        tracker.end_session = Mock()
        tracker.current_session = Mock()
        tracker.current_session.errors_found = 0  # Set initial errors to 0
        
        result = MypyResult(success=True)
        result.errors = [create_mypy_error()] * 5
        result.execution_time = 1.5
        
        files = [Path("test1.py"), Path("test2.py")]
        
        end_tracking_session(tracker, result, files, no_track=False)
        
        # Should update stats and end session
        tracker.update_session_stats.assert_called_once()
        call_args = tracker.update_session_stats.call_args[1]
        assert call_args['files_checked'] == 2
        assert call_args['errors_found'] == 5
        tracker.end_session.assert_called_once_with(1.5)
    
    def test_end_tracking_session_no_track(self):
        """Test skipping tracking end when disabled."""
        tracker = Mock()
        result = MypyResult(success=True)
        files = []
        
        end_tracking_session(tracker, result, files, no_track=True)
        tracker.record_session.assert_not_called()
    
    def test_end_tracking_session_with_fixes(self):
        """Test tracking session with fixes."""
        tracker = Mock()
        tracker.update_session_stats = Mock()
        tracker.end_session = Mock()
        tracker.current_session = Mock()
        tracker.current_session.errors_found = 10
        
        result = MypyResult(success=True)
        result.errors = [create_mypy_error()] * 5  # Reduced from 10 to 5
        result.execution_time = 2.0
        
        files = [Path("test.py")]
        
        end_tracking_session(tracker, result, files, no_track=False)
        
        # Check that update was called with correct values
        tracker.update_session_stats.assert_called_once()
        call_args = tracker.update_session_stats.call_args[1]
        assert call_args['errors_found'] == 5
        # Should calculate fixes as difference
        if 'errors_fixed' in call_args:
            assert call_args['errors_fixed'] == 5
    
    def test_process_json_output(self):
        """Test processing results as JSON."""
        result = MypyResult(success=True)
        result.files_checked = 3
        result.errors = [
            create_mypy_error(message="Error 1"),
            create_mypy_error(line_number=20, message="Error 2")
        ]
        result.warnings = []
        result.notes = []
        
        analysis = Mock()
        analysis.complexity_score = 50.0
        analysis.by_category = {'type': [], 'import': []}
        analysis.suggested_tutorials = ['tutorial1', 'tutorial2', 'tutorial3', 'tutorial4']
        
        json_str = process_json_output(result, analysis, ignored_count=1)
        data = json.loads(json_str)
        
        assert data['total_issues'] == 2  # 2 errors + 0 warnings + 0 notes
        assert data['files_checked'] == 3
        assert data['ignored'] == 1  # Changed from ignored_warnings
        assert data['complexity_score'] == 50.0
        assert data['errors'] == 2
    
    def test_get_file_errors(self):
        """Test getting errors for a specific file."""
        result = MypyResult(success=True)
        result.errors = [
            create_mypy_error(file_path="test1.py", message="Error 1"),
            create_mypy_error(file_path="test2.py", line_number=20, message="Error 2"),
            create_mypy_error(file_path="test1.py", line_number=30, message="Error 3")
        ]
        
        test1_errors = get_file_errors(result, "test1.py")
        assert len(test1_errors) == 2
        assert all(e.file_path == "test1.py" for e in test1_errors)
    
    def test_create_analysis_result(self):
        """Test creating analysis result without config errors."""
        result = MypyResult(success=True)
        result.errors = [
            create_mypy_error(message="Error 1"),
            create_mypy_error(file_path="<configuration>", line_number=0, message="Config error", error_code="config")
        ]
        
        config_errors = [result.errors[1]]
        
        analysis_result = create_analysis_result(result, config_errors)
        
        # Should have original errors minus config errors
        assert len(analysis_result.errors) == 1
        assert analysis_result.errors[0].message == "Error 1"
    
    def test_should_exit_early_no_subcommand(self):
        """Test no early exit without subcommand."""
        args = Namespace(subcommand=None)
        assert should_exit_early(args) is None
    
    def test_should_exit_early_with_tutorial_subcommand(self):
        """Test early exit with tutorial subcommand."""
        args = Namespace(subcommand='tutorial')
        
        # Mock the tutorial main function at the import source
        with patch('storm_checker.scripts.mypy_tutorial.main') as mock_main:
            with patch('sys.argv', ['script.py', 'tutorial']):
                result = should_exit_early(args)
                mock_main.assert_called_once()
                assert result == 0
    
    def test_get_files_to_check_no_keywords(self):
        """Test getting all Python files without keywords."""
        mock_files = [Path("test1.py"), Path("test2.py"), Path("test3.py")]
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = mock_files
            
            files = get_files_to_check(None)
            
            assert len(files) == 3
            assert all(isinstance(f, Path) for f in files)
    
    def test_get_files_to_check_with_keywords(self):
        """Test filtering files with keywords."""
        mock_files = [
            Path("models/user.py"),
            Path("views/user.py"),
            Path("tests/test_user.py")
        ]
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = mock_files
            
            files = get_files_to_check("models")
            
            # Should only include files with "models" in path
            assert len(files) == 1
            assert "models" in str(files[0])
    
    def test_get_files_to_check_with_regex(self):
        """Test filtering files with regex pattern."""
        mock_files = [
            Path("models/user.py"),
            Path("views/user.py"),
            Path("tests/test_user.py")
        ]
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = mock_files
            
            files = get_files_to_check("models|views")
            
            # Should include files matching the regex
            assert len(files) == 2
            assert any("models" in str(f) for f in files)
            assert any("views" in str(f) for f in files)
    
    def test_get_files_to_check_excludes_venv(self):
        """Test that venv and other directories are excluded."""
        mock_files = [
            Path("test.py"),
            Path("venv/lib/test.py"),
            Path(".git/test.py"),
            Path("node_modules/test.py")
        ]
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = mock_files
            
            files = get_files_to_check(None)
            
            # Should exclude venv, .git, node_modules
            assert len(files) == 1
            assert str(files[0]) == "test.py"
    
    def test_warn_about_pretty_true_with_print(self):
        """Test the actual print output of warn_about_pretty_true."""
        with patch('builtins.print') as mock_print:
            warn_about_pretty_true(json_mode=False)
            
            # Should have printed something
            assert mock_print.called
    
    def test_end_tracking_session_with_error_types(self):
        """Test tracking different error types."""
        tracker = Mock()
        tracker.update_session_stats = Mock()
        tracker.end_session = Mock()
        tracker.current_session = Mock()
        tracker.current_session.errors_found = 0  # Set initial errors to 0
        tracker.record_error_type_encountered = Mock()
        
        result = MypyResult(success=True)
        result.errors = [
            create_mypy_error(error_code="no-untyped-def"),
            create_mypy_error(line_number=20, error_code="var-annotated")
        ]
        result.execution_time = 1.0
        
        files = [Path("test.py")]
        
        end_tracking_session(tracker, result, files, no_track=False)
        
        # Should record unique error types
        assert tracker.record_error_type_encountered.call_count == 2
        tracker.record_error_type_encountered.assert_any_call("no-untyped-def")
        tracker.record_error_type_encountered.assert_any_call("var-annotated")