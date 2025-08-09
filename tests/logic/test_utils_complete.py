"""
Comprehensive Tests for Utils Module
====================================
Complete test coverage for all utility functions in utils.py.
"""

import pytest
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from storm_checker.logic.utils import (
    find_python_files, get_git_info, detect_ai_context,
    load_config, get_data_directory, get_config_directory,
    ensure_directory, format_time_delta, parse_file_line_reference,
    calculate_file_stats, get_project_type, DEFAULT_EXCLUDE_DIRS
)


class TestFindPythonFiles:
    """Test find_python_files function comprehensively."""
    
    def test_find_python_files_basic(self, tmp_path):
        """Test basic Python file discovery."""
        # Create test structure
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.py").touch()
        (tmp_path / "not_python.txt").touch()
        
        files = find_python_files(root_path=tmp_path)
        
        assert len(files) == 3
        assert all(f.suffix == ".py" for f in files)
        assert all(isinstance(f, Path) for f in files)
    
    def test_find_python_files_with_keywords(self, tmp_path):
        """Test file discovery with keyword filtering."""
        (tmp_path / "model_user.py").touch()
        (tmp_path / "model_product.py").touch()
        (tmp_path / "view_user.py").touch()
        (tmp_path / "test_models.py").touch()
        
        # Test with simple keyword
        files = find_python_files(root_path=tmp_path, keywords="model")
        assert len(files) == 3  # model_user, model_product, test_models
        
        # Test with regex pattern 
        files = find_python_files(root_path=tmp_path, keywords="model_.*\\.py")
        assert len(files) == 2  # model_user, model_product
        
        # Test case insensitive
        files = find_python_files(root_path=tmp_path, keywords="MODEL")
        assert len(files) == 3
    
    def test_find_python_files_exclude_dirs(self, tmp_path):
        """Test exclusion of specific directories."""
        (tmp_path / "main.py").touch()
        (tmp_path / "venv").mkdir()
        (tmp_path / "venv" / "lib.py").touch()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cached.py").touch()
        (tmp_path / "custom_exclude").mkdir()
        (tmp_path / "custom_exclude" / "excluded.py").touch()
        
        # Test with default exclusions (venv and __pycache__ should be excluded)
        files = find_python_files(root_path=tmp_path)
        assert len(files) == 2  # main.py and custom_exclude/excluded.py
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "excluded.py" in file_names
        
        # Test with custom exclusions
        files = find_python_files(
            root_path=tmp_path,
            exclude_dirs={"custom_exclude"}
        )
        # Should exclude only custom_exclude, so main.py + venv/lib.py + __pycache__/cached.py
        assert len(files) == 3
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "lib.py" in file_names
        assert "cached.py" in file_names
    
    def test_find_python_files_include_patterns(self, tmp_path):
        """Test with custom include patterns."""
        (tmp_path / "script.py").touch()
        (tmp_path / "stub.pyi").touch()
        (tmp_path / "config.yaml").touch()
        
        # Include both .py and .pyi files
        files = find_python_files(
            root_path=tmp_path,
            include_patterns=["*.py", "*.pyi"]
        )
        assert len(files) == 2
        assert any(f.suffix == ".pyi" for f in files)
    
    def test_find_python_files_exclude_patterns(self, tmp_path):
        """Test with exclude patterns."""
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "test_utils.py").touch()
        (tmp_path / "conftest.py").touch()
        
        # Exclude test files
        files = find_python_files(
            root_path=tmp_path,
            exclude_patterns=["test_*.py", "conftest.py"]
        )
        assert len(files) == 1
        assert files[0].name == "main.py"
    
    def test_find_python_files_combined_filters(self, tmp_path):
        """Test with all filters combined."""
        # Create complex structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "models.py").touch()
        (tmp_path / "src" / "views.py").touch()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_models.py").touch()
        (tmp_path / "venv").mkdir()
        (tmp_path / "venv" / "lib.py").touch()
        
        files = find_python_files(
            root_path=tmp_path,
            keywords="models",
            exclude_dirs=DEFAULT_EXCLUDE_DIRS,
            exclude_patterns=["test_*.py"]
        )
        
        assert len(files) == 1
        assert files[0].name == "models.py"


class TestGitInfo:
    """Test git information functions."""
    
    def test_get_git_info_success(self):
        """Test successful git info retrieval."""
        with patch('subprocess.run') as mock_run:
            # Mock successful git commands
            mock_run.side_effect = [
                Mock(returncode=0, stdout="a1b2c3d4e5f6g7h8"),  # commit hash
                Mock(returncode=0, stdout="main"),  # branch
                Mock(returncode=0, stdout="John Doe"),  # author
                Mock(returncode=0, stdout="john@example.com"),  # email
                Mock(returncode=0, stdout="M file.py\n"),  # status (dirty)
            ]
            
            info = get_git_info()
            
            assert info["commit"] == "a1b2c3d4"  # First 8 chars
            assert info["branch"] == "main"
            assert info["author"] == "John Doe"
            assert info["email"] == "john@example.com"
            assert info["is_dirty"] is True
    
    def test_get_git_info_clean_repo(self):
        """Test git info for clean repository."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="abcdef12"),
                Mock(returncode=0, stdout="develop"),
                Mock(returncode=0, stdout="Jane"),
                Mock(returncode=0, stdout="jane@test.com"),
                Mock(returncode=0, stdout=""),  # Clean status
            ]
            
            info = get_git_info()
            assert info["is_dirty"] is False
    
    def test_get_git_info_not_git_repo(self):
        """Test when not in a git repository."""
        with patch('subprocess.run') as mock_run:
            # All commands fail
            mock_run.return_value = Mock(returncode=1, stdout="")
            
            info = get_git_info()
            
            assert info["commit"] is None
            assert info["branch"] is None
            assert info["author"] is None
            assert info["email"] is None
            assert info["is_dirty"] is None
    
    def test_get_git_info_git_not_installed(self):
        """Test when git is not installed."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            info = get_git_info()
            
            assert all(v is None for v in info.values())
    
    def test_get_git_info_partial_failure(self):
        """Test when some git commands fail."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="abc123"),  # commit works
                Mock(returncode=1, stdout=""),  # branch fails
                Mock(returncode=0, stdout="User"),  # author works
                Mock(returncode=1, stdout=""),  # email fails
                Mock(returncode=0, stdout=""),  # status works
            ]
            
            info = get_git_info()
            
            assert info["commit"] == "abc123"
            assert info["branch"] is None
            assert info["author"] == "User"
            assert info["email"] is None
            assert info["is_dirty"] is False


class TestAIDetection:
    """Test AI context detection."""
    
    def test_detect_ai_context_claude(self):
        """Test Claude AI detection."""
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            author_type, model = detect_ai_context()
            assert author_type == "ai_agent"
            assert model == "claude"
    
    def test_detect_ai_context_copilot(self):
        """Test GitHub Copilot detection."""
        with patch.dict(os.environ, {"GITHUB_COPILOT_ACTIVE": "1"}, clear=True):
            author_type, model = detect_ai_context()
            assert author_type == "ai_agent"
            assert model == "copilot"
    
    def test_detect_ai_context_cursor(self):
        """Test Cursor AI detection."""
        with patch.dict(os.environ, {"CURSOR_AI_ACTIVE": "1"}, clear=True):
            author_type, model = detect_ai_context()
            assert author_type == "ai_agent"
            assert model == "cursor"
    
    def test_detect_ai_context_windsurf(self):
        """Test Windsurf/Codeium detection."""
        with patch.dict(os.environ, {"WINDSURF_ACTIVE": "1"}, clear=True):
            author_type, model = detect_ai_context()
            assert author_type == "ai_agent"
            assert model == "windsurf"
    
    def test_detect_ai_context_cody(self):
        """Test Cody detection."""
        with patch.dict(os.environ, {"CODY_ACTIVE": "1"}, clear=True):
            author_type, model = detect_ai_context()
            assert author_type == "ai_agent"
            assert model == "cody"
    
    def test_detect_ai_context_tabnine(self):
        """Test Tabnine detection."""
        with patch.dict(os.environ, {"TABNINE_ACTIVE": "1"}, clear=True):
            author_type, model = detect_ai_context()
            assert author_type == "ai_agent"
            assert model == "tabnine"
    
    def test_detect_ai_context_kite(self):
        """Test Kite detection."""
        with patch.dict(os.environ, {"KITE_ACTIVE": "1"}, clear=True):
            author_type, model = detect_ai_context()
            assert author_type == "ai_agent"
            assert model == "kite"
    
    def test_detect_ai_context_generic(self):
        """Test generic AI detection."""
        with patch.dict(os.environ, {"AI_ASSISTANT": "1"}, clear=True):
            author_type, model = detect_ai_context()
            assert author_type == "ai_agent"
            assert model == "generic"
    
    def test_detect_ai_context_human(self):
        """Test human (no AI) detection."""
        with patch.dict(os.environ, {}, clear=True):
            author_type, model = detect_ai_context()
            assert author_type == "human"
            assert model is None


class TestConfigHandling:
    """Test configuration loading and directories."""
    
    def test_load_config_json(self, tmp_path):
        """Test loading JSON configuration."""
        config_file = tmp_path / "config.json"
        config_data = {"theme": "dark", "verbose": True, "limit": 100}
        config_file.write_text(json.dumps(config_data))
        
        loaded = load_config(config_file)
        assert loaded == config_data
    
    def test_load_config_toml(self, tmp_path):
        """Test loading TOML configuration."""
        try:
            import tomli
            config_file = tmp_path / "config.toml"
            config_file.write_text('[tool]\nname = "test"')
            
            loaded = load_config(config_file)
            assert loaded == {"tool": {"name": "test"}}
        except ImportError:
            # If tomli not available, test that ImportError is properly raised
            config_file = tmp_path / "config.toml"
            config_file.write_text('[tool]\nname = "test"')
            
            with pytest.raises(ImportError):
                load_config(config_file)
    
    def test_load_config_toml_not_installed(self, tmp_path):
        """Test TOML loading when tomli not installed."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("key = 'value'")
        
        # Mock import to raise ImportError for tomli
        original_import = __import__
        def mock_import(name, *args, **kwargs):
            if name == 'tomli':
                raise ImportError("No module named 'tomli'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with pytest.raises(ImportError):
                load_config(config_file)
    
    def test_load_config_file_not_found(self):
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.json"))
    
    def test_load_config_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            load_config(config_file)
    
    def test_load_config_unknown_extension(self, tmp_path):
        """Test auto-detection with unknown extension."""
        config_file = tmp_path / "config.conf"
        
        # First try JSON
        config_file.write_text('{"key": "value"}')
        loaded = load_config(config_file)
        assert loaded == {"key": "value"}
        
        # Then try invalid format that will fail both JSON and TOML parsing
        config_file.write_text("not json or toml")
        # The actual implementation will try JSON first (JSONDecodeError), then TOML (TOMLDecodeError)
        # Since tomli is available in our test environment, it will try TOML parsing and fail
        # We need to either mock tomli to not be available or expect the TOMLDecodeError
        original_import = __import__
        def mock_import(name, *args, **kwargs):
            if name == 'tomli':
                raise ImportError("No module named 'tomli'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with pytest.raises(ValueError, match="Unknown configuration format"):
                load_config(config_file)
    
    def test_get_data_directory_windows(self):
        """Test data directory on Windows."""
        with patch('platform.system', return_value='Windows'):
            with patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"}):
                data_dir = get_data_directory()
                # Path separators may vary based on the system running tests
                assert "StormChecker" in str(data_dir)
                assert "Local" in str(data_dir)
    
    def test_get_data_directory_windows_no_env(self):
        """Test Windows data directory without LOCALAPPDATA."""
        with patch('platform.system', return_value='Windows'):
            with patch.dict(os.environ, {}, clear=True):
                with patch('pathlib.Path.home', return_value=Path("C:\\Users\\Test")):
                    data_dir = get_data_directory()
                    assert "AppData" in str(data_dir)
                    assert "StormChecker" in str(data_dir)
    
    def test_get_data_directory_macos(self):
        """Test data directory on macOS."""
        with patch('platform.system', return_value='Darwin'):
            with patch('pathlib.Path.home', return_value=Path("/Users/test")):
                data_dir = get_data_directory()
                assert str(data_dir) == "/Users/test/Library/Application Support/StormChecker"
    
    def test_get_data_directory_linux(self):
        """Test data directory on Linux."""
        with patch('platform.system', return_value='Linux'):
            with patch('pathlib.Path.home', return_value=Path("/home/test")):
                # Without XDG_DATA_HOME
                data_dir = get_data_directory()
                assert str(data_dir) == "/home/test/.local/share/stormchecker"
    
    def test_get_data_directory_linux_xdg(self):
        """Test Linux data directory with XDG_DATA_HOME."""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {"XDG_DATA_HOME": "/custom/data"}):
                data_dir = get_data_directory()
                assert str(data_dir) == "/custom/data/stormchecker"
    
    def test_get_config_directory_windows(self):
        """Test config directory on Windows."""
        with patch('platform.system', return_value='Windows'):
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
                config_dir = get_config_directory()
                # Path separators may vary based on the system running tests
                assert "StormChecker" in str(config_dir)
                assert "Roaming" in str(config_dir)
    
    def test_get_config_directory_macos(self):
        """Test config directory on macOS."""
        with patch('platform.system', return_value='Darwin'):
            with patch('pathlib.Path.home', return_value=Path("/Users/test")):
                config_dir = get_config_directory()
                assert str(config_dir) == "/Users/test/Library/Preferences/StormChecker"
    
    def test_get_config_directory_linux(self):
        """Test config directory on Linux."""
        with patch('platform.system', return_value='Linux'):
            with patch('pathlib.Path.home', return_value=Path("/home/test")):
                config_dir = get_config_directory()
                assert str(config_dir) == "/home/test/.config/stormchecker"
    
    def test_get_config_directory_linux_xdg(self):
        """Test Linux config directory with XDG_CONFIG_HOME."""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
                config_dir = get_config_directory()
                assert str(config_dir) == "/custom/config/stormchecker"


class TestUtilityFunctions:
    """Test various utility functions."""
    
    def test_ensure_directory(self, tmp_path):
        """Test directory creation."""
        new_dir = tmp_path / "new" / "nested" / "directory"
        assert not new_dir.exists()
        
        result = ensure_directory(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir
        
        # Test idempotency
        result2 = ensure_directory(new_dir)
        assert result2 == new_dir
    
    def test_format_time_delta_microseconds(self):
        """Test time formatting for microseconds."""
        assert format_time_delta(0.0000005) == "0μs"  # 0.5 microseconds rounds to 0
        assert format_time_delta(0.000001) == "1μs"   # 1 microsecond  
        assert format_time_delta(0.000999) == "999μs"
    
    def test_format_time_delta_milliseconds(self):
        """Test time formatting for milliseconds."""
        assert format_time_delta(0.001) == "1ms"
        assert format_time_delta(0.123) == "123ms"
        assert format_time_delta(0.999) == "999ms"
    
    def test_format_time_delta_seconds(self):
        """Test time formatting for seconds."""
        assert format_time_delta(1.0) == "1.0s"
        assert format_time_delta(45.5) == "45.5s"
        assert format_time_delta(59.9) == "59.9s"
    
    def test_format_time_delta_minutes(self):
        """Test time formatting for minutes."""
        assert format_time_delta(60) == "1m 0s"
        assert format_time_delta(90) == "1m 30s"
        assert format_time_delta(3599) == "59m 59s"
    
    def test_format_time_delta_hours(self):
        """Test time formatting for hours."""
        assert format_time_delta(3600) == "1h 0m 0s"
        assert format_time_delta(3665) == "1h 1m 5s"
        assert format_time_delta(7200) == "2h 0m 0s"
        assert format_time_delta(10000) == "2h 46m 40s"
    
    def test_parse_file_line_reference_with_line(self):
        """Test parsing file:line references."""
        file_path, line = parse_file_line_reference("src/models.py:42")
        assert file_path == "src/models.py"
        assert line == 42
    
    def test_parse_file_line_reference_without_line(self):
        """Test parsing file reference without line number."""
        file_path, line = parse_file_line_reference("src/models.py")
        assert file_path == "src/models.py"
        assert line is None
    
    def test_parse_file_line_reference_invalid_line(self):
        """Test parsing with invalid line number."""
        file_path, line = parse_file_line_reference("src/models.py:abc")
        assert file_path == "src/models.py"
        assert line is None
    
    def test_parse_file_line_reference_with_colon_in_path(self):
        """Test parsing with colon in file path."""
        # Windows-style path - the function splits on first colon
        file_path, line = parse_file_line_reference("C:\\Users\\file.py:10")
        # Split on first colon, so "C" and "\\Users\\file.py:10"
        assert file_path == "C"  # First part before first colon
        assert line is None  # "\\Users\\file.py:10" is not a valid int


class TestFileStats:
    """Test file statistics calculation."""
    
    def test_calculate_file_stats_basic(self, tmp_path):
        """Test basic file statistics."""
        py_file = tmp_path / "test.py"
        py_file.write_text('''"""Module docstring."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    # This is a comment
    return a + b

def multiply(x, y):
    return x * y

# Another comment
class MyClass:
    pass''')
        
        stats = calculate_file_stats(py_file)
        
        assert stats["total_lines"] == 13
        assert stats["blank_lines"] == 3   # Lines 2, 7, 10
        assert stats["comment_lines"] == 2
        assert stats["docstring_lines"] == 2
        assert stats["code_lines"] == 6   # def add, return a+b, def multiply, return x*y, class MyClass, pass
        assert stats["type_hint_score"] == 50.0  # 1 of 2 functions has type hints
    
    def test_calculate_file_stats_multiline_docstring(self, tmp_path):
        """Test with multiline docstrings."""
        py_file = tmp_path / "test.py"
        py_file.write_text('''"""
        Multi-line
        module
        docstring.
        """

def func():
    """
    Another multi-line
    docstring.
    """
    pass
''')
        
        stats = calculate_file_stats(py_file)
        assert stats["docstring_lines"] == 9
    
    def test_calculate_file_stats_single_quotes(self, tmp_path):
        """Test with single-quote docstrings."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""'''Single quote docstring.'''

def func():
    '''Another one.'''
    pass
""")
        
        stats = calculate_file_stats(py_file)
        assert stats["docstring_lines"] == 2
    
    def test_calculate_file_stats_no_functions(self, tmp_path):
        """Test file with no functions."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""# Just comments
x = 1
y = 2
""")
        
        stats = calculate_file_stats(py_file)
        assert stats["type_hint_score"] == 0.0
    
    def test_calculate_file_stats_all_typed(self, tmp_path):
        """Test file with all functions typed."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def func1() -> None:
    pass

def func2(x: int) -> int:
    return x

def func3(s: str) -> str:
    return s
""")
        
        stats = calculate_file_stats(py_file)
        assert stats["type_hint_score"] == 100.0
    
    def test_calculate_file_stats_file_not_found(self):
        """Test with non-existent file."""
        stats = calculate_file_stats(Path("/nonexistent/file.py"))
        
        assert stats["total_lines"] == 0
        assert stats["type_hint_score"] == 0.0
    
    def test_calculate_file_stats_unicode_error(self, tmp_path):
        """Test with file that can't be decoded."""
        py_file = tmp_path / "test.py"
        # Write binary data that's not valid UTF-8
        py_file.write_bytes(b'\xff\xfe\x00\x00')
        
        stats = calculate_file_stats(py_file)
        assert stats["total_lines"] == 0


class TestProjectTypeDetection:
    """Test project type detection."""
    
    def test_get_project_type_django(self, tmp_path):
        """Test Django project detection."""
        (tmp_path / "manage.py").touch()
        
        project_type = get_project_type(tmp_path)
        assert project_type == "django"
    
    def test_get_project_type_fastapi(self, tmp_path):
        """Test FastAPI project detection."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("fastapi==0.68.0\nuvicorn==0.15.0")
        
        project_type = get_project_type(tmp_path)
        assert project_type == "fastapi"
    
    def test_get_project_type_flask(self, tmp_path):
        """Test Flask project detection."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("Flask==2.0.1\ngunicorn==20.1.0")
        
        project_type = get_project_type(tmp_path)
        assert project_type == "flask"
    
    def test_get_project_type_jupyter(self, tmp_path):
        """Test Jupyter notebook project detection."""
        (tmp_path / "analysis.ipynb").touch()
        (tmp_path / "data_exploration.ipynb").touch()
        
        project_type = get_project_type(tmp_path)
        assert project_type == "jupyter"
    
    def test_get_project_type_package(self, tmp_path):
        """Test package project detection."""
        (tmp_path / "setup.py").touch()
        
        project_type = get_project_type(tmp_path)
        assert project_type == "package"
    
    def test_get_project_type_package_pyproject(self, tmp_path):
        """Test package detection with pyproject.toml."""
        (tmp_path / "pyproject.toml").touch()
        
        project_type = get_project_type(tmp_path)
        assert project_type == "package"
    
    def test_get_project_type_script(self, tmp_path):
        """Test simple script detection."""
        (tmp_path / "script.py").touch()
        (tmp_path / "helper.py").touch()
        
        project_type = get_project_type(tmp_path)
        assert project_type == "script"
    
    def test_get_project_type_unknown(self, tmp_path):
        """Test unknown project type."""
        # Create many Python files (more than script threshold)
        for i in range(5):
            (tmp_path / f"file{i}.py").touch()
        
        project_type = get_project_type(tmp_path)
        assert project_type == "unknown"
    
    def test_get_project_type_requirements_in(self, tmp_path):
        """Test detection with requirements.in file."""
        req_file = tmp_path / "requirements.in"
        req_file.write_text("fastapi")
        
        project_type = get_project_type(tmp_path)
        assert project_type == "fastapi"
    
    def test_get_project_type_pyproject_toml(self, tmp_path):
        """Test detection with pyproject.toml dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.poetry.dependencies]\nflask = '^2.0.0'")
        
        project_type = get_project_type(tmp_path)
        assert project_type == "flask"
    
    def test_get_project_type_setup_py(self, tmp_path):
        """Test detection with setup.py dependencies."""
        setup = tmp_path / "setup.py"
        setup.write_text("install_requires=['fastapi>=0.68.0']")
        
        project_type = get_project_type(tmp_path)
        assert project_type == "fastapi"
    
    def test_get_project_type_unreadable_requirements(self, tmp_path):
        """Test with unreadable requirements file."""
        req_file = tmp_path / "requirements.txt"
        req_file.touch()
        req_file.chmod(0o000)
        
        try:
            project_type = get_project_type(tmp_path)
            # Should continue checking other indicators
            assert project_type in ["unknown", "package", "script"]
        finally:
            # Restore permissions for cleanup
            req_file.chmod(0o644)