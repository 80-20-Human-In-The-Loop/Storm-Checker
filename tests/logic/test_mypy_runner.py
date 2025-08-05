"""
Tests for MyPy Runner
=====================
Test MyPy execution and result parsing.
"""

import pytest
import sys
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logic.mypy_runner import MypyError, MypyResult, MypyRunner
from tests.test_utils import TestFileBuilder, temporary_cwd


class TestMypyError:
    """Test MypyError data model."""
    
    def test_mypy_error_creation(self):
        """Test creating MypyError."""
        error = MypyError(
            file_path="src/main.py",
            line_number=10,
            column=5,
            severity="error",
            error_code="no-untyped-def",
            message="Function is missing a type annotation",
            raw_line="src/main.py:10:5: error: Function is missing a type annotation  [no-untyped-def]"
        )
        
        assert error.file_path == "src/main.py"
        assert error.line_number == 10
        assert error.column == 5
        assert error.severity == "error"
        assert error.error_code == "no-untyped-def"
        
    def test_mypy_error_string_representation(self):
        """Test string representation of MypyError."""
        error = MypyError(
            file_path="test.py",
            line_number=5,
            column=10,
            severity="error",
            error_code="return-value",
            message="Incompatible return value",
            raw_line=""
        )
        
        result = str(error)
        assert "test.py:5:10" in result
        assert "error" in result
        assert "Incompatible return value" in result
        assert "[return-value]" in result
        
    def test_mypy_error_no_column(self):
        """Test MypyError without column number."""
        error = MypyError(
            file_path="test.py",
            line_number=5,
            column=None,
            severity="warning",
            error_code="unused-ignore",
            message="Unused ignore comment",
            raw_line=""
        )
        
        result = str(error)
        assert "test.py:5:" in result
        assert ":5::" not in result  # Should not have double colons
        
    def test_mypy_error_no_code(self):
        """Test MypyError without error code."""
        error = MypyError(
            file_path="test.py",
            line_number=5,
            column=10,
            severity="error",
            error_code=None,
            message="Some error",
            raw_line=""
        )
        
        result = str(error)
        assert "[" not in result  # Should not have error code brackets


class TestMypyResult:
    """Test MypyResult data model."""
    
    def test_mypy_result_creation(self):
        """Test creating MypyResult."""
        errors = [
            MypyError("test.py", 1, 1, "error", "test", "Test error", ""),
            MypyError("test.py", 2, 1, "error", "test", "Another error", "")
        ]
        warnings = [
            MypyError("test.py", 3, 1, "warning", "test", "Test warning", "")
        ]
        
        result = MypyResult(
            success=False,
            errors=errors,
            warnings=warnings,
            notes=[],
            files_checked=3,
            execution_time=1.5,
            command=["mypy", "src/"],
            return_code=1,
            raw_output="Test output"
        )
        
        assert not result.success
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.files_checked == 3
        assert result.execution_time == 1.5
        
    def test_total_issues_property(self):
        """Test total_issues property."""
        result = MypyResult(
            success=True,
            errors=[Mock(), Mock()],
            warnings=[Mock()],
            notes=[Mock(), Mock(), Mock()]
        )
        
        assert result.total_issues == 6
        
    def test_has_errors_property(self):
        """Test has_errors property."""
        # With errors
        result = MypyResult(success=True, errors=[Mock()])
        assert result.has_errors
        
        # Without errors
        result = MypyResult(success=True, errors=[])
        assert not result.has_errors
        
    def test_get_errors_by_file(self):
        """Test grouping errors by file."""
        errors = [
            MypyError("file1.py", 1, 1, "error", "test", "Error 1", ""),
            MypyError("file2.py", 1, 1, "error", "test", "Error 2", ""),
            MypyError("file1.py", 2, 1, "error", "test", "Error 3", ""),
        ]
        
        result = MypyResult(success=False, errors=errors)
        by_file = result.get_errors_by_file()
        
        assert len(by_file) == 2
        assert len(by_file["file1.py"]) == 2
        assert len(by_file["file2.py"]) == 1


class TestMypyRunner:
    """Test MypyRunner class."""
    
    def test_mypy_runner_initialization(self):
        """Test MypyRunner initialization."""
        runner = MypyRunner()
        assert hasattr(runner, 'mypy_executable')
        assert hasattr(runner, 'parse_error_line')
        
    def test_parse_standard_error_line(self):
        """Test parsing standard error line."""
        runner = MypyRunner()
        line = "src/main.py:10:5: error: Function is missing a type annotation  [no-untyped-def]"
        
        error = runner.parse_error_line(line)
        
        assert error is not None
        assert error.file_path == "src/main.py"
        assert error.line_number == 10
        assert error.column == 5
        assert error.severity == "error"
        assert error.error_code == "no-untyped-def"
        assert error.message == "Function is missing a type annotation"
        
    def test_parse_error_without_column(self):
        """Test parsing error line without column."""
        runner = MypyRunner()
        line = "src/utils.py:25: warning: Unused 'type: ignore' comment"
        
        error = runner.parse_error_line(line)
        
        assert error is not None
        assert error.file_path == "src/utils.py"
        assert error.line_number == 25
        assert error.column is None
        assert error.severity == "warning"
        
    def test_parse_error_with_complex_message(self):
        """Test parsing error with complex message."""
        runner = MypyRunner()
        line = 'test.py:5:10: error: Incompatible return value type (got "int", expected "str")  [return-value]'
        
        error = runner.parse_error_line(line)
        
        assert error is not None
        assert error.message == 'Incompatible return value type (got "int", expected "str")'
        assert error.error_code == "return-value"
        
    def test_parse_invalid_lines(self):
        """Test parsing invalid lines returns None."""
        runner = MypyRunner()
        
        invalid_lines = [
            "",
            "Not an error line",
            "Success: no issues found in 3 source files",
            "Found 2 errors in 1 file (checked 3 source files)"
        ]
        
        for line in invalid_lines:
            assert runner.parse_error_line(line) is None
            
    @patch('subprocess.run')
    def test_run_mypy_success(self, mock_run):
        """Test running MyPy with success."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success: no issues found in 3 source files\n",
            stderr=""
        )
        
        runner = MypyRunner()
        result = runner.run_mypy([Path("src/")])
        
        assert result.success
        assert result.return_code == 0
        assert len(result.errors) == 0
        assert result.files_checked == 1  # We passed 1 file to run_mypy
        
    @patch('subprocess.run')
    def test_run_mypy_with_errors(self, mock_run):
        """Test running MyPy with errors."""
        output = """src/main.py:10:5: error: Function is missing a type annotation  [no-untyped-def]
src/utils.py:25:10: error: Incompatible return value type (got "int", expected "str")  [return-value]
Found 2 errors in 2 files (checked 5 source files)
"""
        
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=output,
            stderr=""
        )
        
        runner = MypyRunner()
        result = runner.run_mypy([Path("src/")])
        
        assert result.success  # success=True when return_code is 1 (errors found but MyPy ran OK)
        assert result.return_code == 1
        assert len(result.errors) == 2
        assert result.files_checked == 1  # We passed 1 file to run_mypy
        
    @patch('subprocess.run')
    def test_run_with_custom_args(self, mock_run):
        """Test running with custom arguments."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success: no issues found",
            stderr=""
        )
        
        runner = MypyRunner()
        result = runner.run_mypy([Path("src/")], additional_args=["--strict", "--show-error-codes"])
        
        # Check that custom args were passed
        call_args = mock_run.call_args[0][0]
        assert "--strict" in call_args
        assert "--show-error-codes" in call_args
        
    @patch('subprocess.run')
    def test_handle_mypy_not_found(self, mock_run):
        """Test handling when MyPy is not found."""
        mock_run.side_effect = FileNotFoundError("mypy not found")
        
        runner = MypyRunner()
        result = runner.run_mypy([Path("src/")])
        
        # Should return a failed result, not raise an exception
        assert not result.success
        assert result.return_code == -1
        assert "MyPy executable not found" in result.raw_output
            
    def test_error_parsing_integration(self):
        """Test that error parsing works with realistic output."""
        runner = MypyRunner()
        
        # Test that we can parse various error formats
        test_lines = [
            "src/main.py:10:5: error: Function is missing a type annotation  [no-untyped-def]",
            "utils.py:25: warning: Unused 'type: ignore' comment",
            "models.py:42:8: note: Revealed type is 'builtins.str'"
        ]
        
        for line in test_lines:
            error = runner.parse_error_line(line)
            assert error is not None
            assert error.file_path
            assert error.line_number > 0
            
    def test_empty_files_list(self):
        """Test running MyPy with empty files list."""
        runner = MypyRunner()
        result = runner.run_mypy([])
        
        assert result.success
        assert result.files_checked == 0
        assert len(result.errors) == 0
        assert result.command == []
    
    def test_mypy_timeout(self):
        """Test handling of MyPy timeout."""
        runner = MypyRunner()
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('mypy', 30)
            
            result = runner.run_mypy([Path('test.py')], timeout=30)
            
            assert not result.success
            assert result.return_code == -1
            assert "timed out" in result.raw_output
            assert result.files_checked == 1
    
    def test_mypy_not_found(self):
        """Test handling when MyPy executable is not found."""
        runner = MypyRunner(mypy_executable='nonexistent-mypy')
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = runner.run_mypy([Path('test.py')])
            
            assert not result.success
            assert result.return_code == -1
            assert "not found" in result.raw_output
            assert result.files_checked == 1
    
    def test_parse_error_line_no_match(self):
        """Test parse_error_line with line that doesn't match pattern."""
        runner = MypyRunner()
        
        # Test various non-matching lines
        assert runner.parse_error_line("This is not an error line") is None
        assert runner.parse_error_line("Found 5 errors in 2 files") is None
        assert runner.parse_error_line("Success: no issues found") is None
    
    def test_filter_ignored_errors_without_checking_files(self):
        """Test filter_ignored_errors with check_source_files=False."""
        runner = MypyRunner()
        
        errors = [
            MypyError("test.py", 10, None, "error", "test-error", "Test error", ""),
            MypyError("test.py", 20, None, "error", "test-error", "Another error", ""),
        ]
        
        genuine, ignored = runner.filter_ignored_errors(errors, check_source_files=False)
        
        assert len(genuine) == 2
        assert len(ignored) == 0
    
    def test_filter_ignored_errors_with_type_ignore(self):
        """Test filter_ignored_errors with type: ignore comments."""
        runner = MypyRunner()
        
        # Create a temporary file with type: ignore comment
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_ignore.py"
            test_file.write_text('''
def bad_function(x):  # type: ignore
    return x + 1

def good_function(x):
    return x + 1
''')
            
            errors = [
                MypyError(str(test_file), 2, None, "error", "no-untyped-def", "No type annotation", ""),
                MypyError(str(test_file), 5, None, "error", "no-untyped-def", "No type annotation", ""),
            ]
            
            genuine, ignored = runner.filter_ignored_errors(errors, check_source_files=True)
            
            assert len(genuine) == 1  # Only line 5 without type: ignore
            assert len(ignored) == 1  # Line 2 with type: ignore
            assert genuine[0].line_number == 5
            assert ignored[0].line_number == 2
    
    def test_has_type_ignore_comment_file_not_found(self):
        """Test _has_type_ignore_comment when file doesn't exist."""
        runner = MypyRunner()
        
        # Test with non-existent file
        assert not runner._has_type_ignore_comment("nonexistent.py", 1)
    
    def test_has_type_ignore_comment_invalid_line(self):
        """Test _has_type_ignore_comment with invalid line numbers."""
        runner = MypyRunner()
        
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("# Just one line")
            
            # Test line number out of range
            assert not runner._has_type_ignore_comment(str(test_file), 0)  # Line 0 invalid
            assert not runner._has_type_ignore_comment(str(test_file), 100)  # Beyond file
    
    def test_parse_mypy_output_config_error(self):
        """Test parsing MyPy output with configuration errors."""
        runner = MypyRunner()
        
        # Test with configuration error in stderr
        stderr = "storm-checker is not a valid Python package name"
        result = runner.parse_mypy_output(
            stdout="",
            stderr=stderr,
            return_code=2,
            files_checked=1,
            execution_time=0.1,
            command=["mypy", "test.py"]
        )
        
        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "config-error"
        assert "not a valid Python package name" in result.errors[0].message
    
    def test_parse_mypy_output_with_errors_prevented(self):
        """Test parsing output when errors prevented further checking."""
        runner = MypyRunner()
        
        stdout = "Error constructing plugin instance"
        result = runner.parse_mypy_output(
            stdout=stdout,
            stderr="",
            return_code=2,
            files_checked=1,
            execution_time=0.1,
            command=["mypy", "test.py"]
        )
        
        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "config-error"
    
    def test_parse_mypy_output_generic_config_error(self):
        """Test parsing output with generic configuration error."""
        runner = MypyRunner()
        
        # Test when no specific pattern matches but return code indicates error
        result = runner.parse_mypy_output(
            stdout="",
            stderr="",
            return_code=2,  # Not 0 or 1
            files_checked=1,
            execution_time=0.1,
            command=["mypy", "test.py"]
        )
        
        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "config-error"
        assert result.errors[0].message == "MyPy configuration error prevented type checking"
    
    def test_check_project_method(self):
        """Test check_project convenience method."""
        runner = MypyRunner()
        
        with patch.object(runner, 'run_mypy') as mock_run:
            mock_result = MypyResult(success=True, files_checked=5)
            mock_run.return_value = mock_result
            
            with patch('logic.mypy_runner.find_python_files') as mock_find:
                mock_find.return_value = [Path(f"test{i}.py") for i in range(5)]
                
                result = runner.check_project(keywords="test")
                
                assert result == mock_result
                mock_find.assert_called_once()
                mock_run.assert_called_once_with(mock_find.return_value)
    
    def test_check_single_file_method(self):
        """Test check_single_file convenience method."""
        runner = MypyRunner()
        
        with patch.object(runner, 'run_mypy') as mock_run:
            mock_result = MypyResult(success=True, files_checked=1)
            mock_run.return_value = mock_result
            
            test_file = Path("test.py")
            result = runner.check_single_file(test_file)
            
            assert result == mock_result
            mock_run.assert_called_once_with([test_file])
    
    def test_parse_mypy_output_with_warnings_and_notes(self):
        """Test parsing output with warnings and notes."""
        runner = MypyRunner()
        
        stdout = """test.py:10:5: error: Function is missing a type annotation  [no-untyped-def]
test.py:20: warning: Unused 'type: ignore' comment
test.py:30:8: note: Revealed type is 'builtins.str'
"""
        
        result = runner.parse_mypy_output(
            stdout=stdout,
            stderr="",
            return_code=1,
            files_checked=1,
            execution_time=0.1,
            command=["mypy", "test.py"]
        )
        
        assert result.success
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.notes) == 1
        
        assert result.errors[0].line_number == 10
        assert result.warnings[0].line_number == 20
        assert result.notes[0].line_number == 30
    
    def test_parse_mypy_output_empty_lines_and_summary(self):
        """Test parsing output with empty lines and summary lines."""
        runner = MypyRunner()
        
        stdout = """test.py:10:5: error: Function is missing a type annotation  [no-untyped-def]

Found 1 error in 1 file (checked 1 source file)
Success: no issues found in 1 source file
"""
        
        result = runner.parse_mypy_output(
            stdout=stdout,
            stderr="",
            return_code=1,
            files_checked=1,
            execution_time=0.1,
            command=["mypy", "test.py"]
        )
        
        # Should only have 1 error, empty and summary lines should be skipped
        assert len(result.errors) == 1
        assert result.errors[0].line_number == 10
    
    def test_parse_mypy_output_generic_error_with_output(self):
        """Test parsing generic error with non-empty output."""
        runner = MypyRunner()
        
        # Test when we have return code 2 and some output
        stderr = """Some error occurred
This is the error message
Another line of error"""
        
        result = runner.parse_mypy_output(
            stdout="",
            stderr=stderr,
            return_code=2,
            files_checked=1,
            execution_time=0.1,
            command=["mypy", "test.py"]
        )
        
        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "config-error"
        # Should use the first non-empty line
        assert result.errors[0].message == "Some error occurred"