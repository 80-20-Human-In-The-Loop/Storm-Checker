"""
Test colors.py behavior when Rich import fails
==============================================
This tests the ImportError handling in colors.py (lines 279-283).
"""

import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_colors_module_with_rich_import_failure():
    """Test colors.py when Rich import fails (lines 279-283)."""
    # Remove any existing imports
    modules_to_remove = [
        'storm_checker.cli.colors',
        'rich',
        'rich.theme',
        'rich.color',
        'rich.style',
        'rich.console',
        'rich.panel',
        'rich.text',
        'rich.table',
        'rich.align'
    ]

    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]

    # Mock the import to fail
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if 'rich' in name:
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = mock_import

    try:
        # Now import colors module - should handle ImportError gracefully
        import storm_checker.cli.colors

        # Verify that RICH_AVAILABLE is False
        assert storm_checker.cli.colors.RICH_AVAILABLE == False
        assert storm_checker.cli.colors.RichTheme is None
        assert storm_checker.cli.colors.RichColor is None
        assert storm_checker.cli.colors.RichStyle is None

        # Test that functions still work without Rich
        # Test get_rich_theme (line 289)
        theme = storm_checker.cli.colors.get_rich_theme()
        assert theme is None

        # Test get_rich_color (line 334)
        color = storm_checker.cli.colors.get_rich_color("primary")
        assert color is None

        # Test create_rich_style (line 352)
        style = storm_checker.cli.colors.create_rich_style("primary")
        assert style is None

        # Test demo_rich_integration (lines 563-564)
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            storm_checker.cli.colors.demo_rich_integration()
            output = sys.stdout.getvalue()
            assert "Rich library not available" in output
        finally:
            sys.stdout = old_stdout

        # Test print_rich_* functions fallback correctly
        sys.stdout = io.StringIO()
        try:
            storm_checker.cli.colors.print_rich_header("Test", "Subtitle")
            output = sys.stdout.getvalue()
            assert "=" in output  # Should use regular header
        finally:
            sys.stdout = old_stdout

        # Test EnhancedColorPrinter with RICH_AVAILABLE=False (lines 374-376)
        result = storm_checker.cli.colors.EnhancedColorPrinter.rich_text("Test", "primary")
        assert "Test" in result

        result = storm_checker.cli.colors.EnhancedColorPrinter.rich_text("Test", "unknown")
        assert result == "Test"

    finally:
        # Restore original import
        builtins.__import__ = original_import


def test_print_rich_functions_with_import_exceptions():
    """Test print_rich_* functions when imports fail inside try blocks."""
    # This tests the exception handlers (lines 455, 469, 481, 493, 505, 517)

    # First ensure storm_checker.cli.colors is loaded normally
    if 'storm_checker.cli.colors' in sys.modules:
        del sys.modules['storm_checker.cli.colors']

    import storm_checker.cli.colors
    from unittest.mock import patch

    # Mock Console import to fail
    import builtins
    original_import = builtins.__import__

    def mock_import_console_fail(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'rich.console' and fromlist and 'Console' in fromlist:
            raise ImportError("Console import failed")
        return original_import(name, globals, locals, fromlist, level)

    # Test each print_rich_* function
    functions_to_test = [
        ('print_rich_success', 'Success', '✅'),
        ('print_rich_error', 'Error', '❌'),
        ('print_rich_warning', 'Warning', '⚠️'),
        ('print_rich_info', 'Info', 'ℹ️'),
        ('print_rich_learn', 'Learn', '📚'),
    ]

    for func_name, message, icon in functions_to_test:
        builtins.__import__ = mock_import_console_fail

        try:
            func = getattr(storm_checker.cli.colors, func_name)

            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                func(message)
                output = sys.stdout.getvalue()
                assert icon in output
                assert message in output
            finally:
                sys.stdout = old_stdout
        finally:
            builtins.__import__ = original_import

    # Test print_rich_header with Panel import failure
    def mock_import_panel_fail(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'rich.panel' and fromlist and 'Panel' in fromlist:
            raise ImportError("Panel import failed")
        return original_import(name, globals, locals, fromlist, level)

    builtins.__import__ = mock_import_panel_fail

    try:
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            storm_checker.cli.colors.print_rich_header("Header", "Subtitle")
            output = sys.stdout.getvalue()
            assert "Header" in output
            assert "=" in output  # Should fallback to regular header
        finally:
            sys.stdout = old_stdout
    finally:
        builtins.__import__ = original_import


def test_demo_rich_integration_with_error():
    """Test demo_rich_integration exception handling."""
    # Remove storm_checker.cli.colors if already loaded
    if 'storm_checker.cli.colors' in sys.modules:
        del sys.modules['storm_checker.cli.colors']

    import storm_checker.cli.colors
    from unittest.mock import patch, MagicMock

    if storm_checker.cli.colors.RICH_AVAILABLE:
        # Mock to make the demo fail and trigger exception handler
        with patch('storm_checker.cli.colors.demo_colors') as mock_demo:
            # First make Console creation succeed but table operations fail
            with patch('rich.table.Table') as MockTable:
                MockTable.side_effect = Exception("Table creation failed")

                import io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                try:
                    storm_checker.cli.colors.demo_rich_integration()
                    output = sys.stdout.getvalue()
                    # Should have called fallback
                    mock_demo.assert_called_once()
                finally:
                    sys.stdout = old_stdout
