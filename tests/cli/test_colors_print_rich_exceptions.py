"""
Test print_rich_* exception handling specifically
=================================================
Focus on catching the exact exception lines.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_print_rich_header_import_error():
    """Test print_rich_header when Console import fails."""
    from storm_checker.cli.colors import RICH_AVAILABLE

    if RICH_AVAILABLE:
        # Mock the imports to fail
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'rich.console' and args and 'Console' in args[2]:
                raise ImportError("Console not available")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = mock_import

        try:
            from storm_checker.cli.colors import print_rich_header
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                print_rich_header("Test")
                output = sys.stdout.getvalue()
                assert "Test" in output
                assert "=" in output  # Should have fallback header
            finally:
                sys.stdout = old_stdout
        finally:
            builtins.__import__ = original_import


def test_print_rich_success_console_print_fails():
    """Test print_rich_success when console.print fails."""
    from storm_checker.cli.colors import RICH_AVAILABLE

    if RICH_AVAILABLE:
        # Create a console that fails on print
        with patch('rich.console.Console') as MockConsole:
            mock_instance = MagicMock()
            mock_instance.print.side_effect = Exception("Print failed")
            MockConsole.return_value = mock_instance

            from storm_checker.cli.colors import print_rich_success

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                print_rich_success("Test message")
                output = sys.stdout.getvalue()
                # Should have fallen back to regular print_success
                assert "✅" in output
                assert "Test message" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_error_console_print_fails():
    """Test print_rich_error when console.print fails."""
    from storm_checker.cli.colors import RICH_AVAILABLE

    if RICH_AVAILABLE:
        with patch('rich.console.Console') as MockConsole:
            mock_instance = MagicMock()
            mock_instance.print.side_effect = Exception("Print failed")
            MockConsole.return_value = mock_instance

            from storm_checker.cli.colors import print_rich_error

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                print_rich_error("Error message")
                output = sys.stdout.getvalue()
                assert "❌" in output
                assert "Error message" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_warning_console_print_fails():
    """Test print_rich_warning when console.print fails."""
    from storm_checker.cli.colors import RICH_AVAILABLE

    if RICH_AVAILABLE:
        with patch('rich.console.Console') as MockConsole:
            mock_instance = MagicMock()
            mock_instance.print.side_effect = Exception("Print failed")
            MockConsole.return_value = mock_instance

            from storm_checker.cli.colors import print_rich_warning

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                print_rich_warning("Warning message")
                output = sys.stdout.getvalue()
                assert "⚠️" in output
                assert "Warning message" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_info_console_print_fails():
    """Test print_rich_info when console.print fails."""
    from storm_checker.cli.colors import RICH_AVAILABLE

    if RICH_AVAILABLE:
        with patch('rich.console.Console') as MockConsole:
            mock_instance = MagicMock()
            mock_instance.print.side_effect = Exception("Print failed")
            MockConsole.return_value = mock_instance

            from storm_checker.cli.colors import print_rich_info

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                print_rich_info("Info message")
                output = sys.stdout.getvalue()
                assert "ℹ️" in output
                assert "Info message" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_learn_console_print_fails():
    """Test print_rich_learn when console.print fails."""
    from storm_checker.cli.colors import RICH_AVAILABLE

    if RICH_AVAILABLE:
        with patch('rich.console.Console') as MockConsole:
            mock_instance = MagicMock()
            mock_instance.print.side_effect = Exception("Print failed")
            MockConsole.return_value = mock_instance

            from storm_checker.cli.colors import print_rich_learn

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                print_rich_learn("Learn message")
                output = sys.stdout.getvalue()
                assert "📚" in output
                assert "Learn message" in output
            finally:
                sys.stdout = old_stdout


def test_demo_rich_integration_table_error():
    """Test demo_rich_integration when Table creation fails."""
    from storm_checker.cli.colors import RICH_AVAILABLE

    if RICH_AVAILABLE:
        # Make Table creation fail but Console work
        with patch('rich.table.Table', side_effect=Exception("Table error")):
            from storm_checker.cli.colors import demo_rich_integration

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                demo_rich_integration()
                output = sys.stdout.getvalue()
                # Should fallback to demo_colors
                assert "Storm-Checker Color Palette" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_header_text_assembly_error():
    """Test print_rich_header when Text assembly fails."""
    from storm_checker.cli.colors import RICH_AVAILABLE

    if RICH_AVAILABLE:
        # Mock Text.assemble to fail
        with patch('rich.text.Text.assemble', side_effect=Exception("Text assembly error")):
            from storm_checker.cli.colors import print_rich_header

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                print_rich_header("Title", "Subtitle")
                output = sys.stdout.getvalue()
                # Should fallback
                assert "Title" in output
                assert "=" in output
            finally:
                sys.stdout = old_stdout
