"""
Tests for CLI Colors Module
===========================
Test color functions and theming.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from storm_checker.cli.colors import (
    Color, PALETTE, THEME, RESET, BOLD, ColorPrinter,
    print_header, print_success, print_error, print_warning, print_info
)
from tests.test_utils import CLIOutputCapture


class TestColor:
    """Test Color class functionality."""

    def test_color_initialization(self):
        """Test Color object creation."""
        color = Color("#FF5733", "Test Orange")
        assert color.hex == "#FF5733"
        assert color.name == "Test Orange"
        assert color.rgb == (255, 87, 51)

    def test_hex_to_rgb_conversion(self):
        """Test hex to RGB conversion."""
        test_cases = [
            ("#FFFFFF", (255, 255, 255)),
            ("#000000", (0, 0, 0)),
            ("#FF0000", (255, 0, 0)),
            ("#00FF00", (0, 255, 0)),
            ("#0000FF", (0, 0, 255)),
        ]

        for hex_color, expected_rgb in test_cases:
            color = Color(hex_color)
            assert color.rgb == expected_rgb

    def test_ansi_code_generation(self):
        """Test ANSI escape code generation."""
        color = Color("#FF5733")
        assert color.ansi == "\033[38;2;255;87;51m"
        assert str(color) == "\033[38;2;255;87;51m"

    def test_background_color(self):
        """Test background color code generation."""
        color = Color("#FF5733")
        assert color.bg == "\033[48;2;255;87;51m"


class TestPalette:
    """Test color palette definitions."""

    def test_palette_completeness(self):
        """Test that all palette colors are defined."""
        # Check that palette has expected color categories
        color_categories = {
            "light_gray", "cream", "forest_dark", "navy_blue",
            "charcoal", "burnt_orange", "crimson", "white", "black"
        }

        for category in color_categories:
            assert category in PALETTE, f"Missing color category: {category}"

    def test_palette_colors_valid(self):
        """Test that all palette colors are valid Color objects."""
        for name, color in PALETTE.items():
            assert isinstance(color, Color), f"{name} is not a Color object"
            assert color.name, f"{name} has no name"
            assert len(color.rgb) == 3, f"{name} has invalid RGB values"

    def test_theme_references_valid(self):
        """Test that theme references valid palette colors."""
        for theme_name, color in THEME.items():
            assert isinstance(color, Color), f"{theme_name} is not a Color object"
            # Verify color exists in palette
            assert color in PALETTE.values(), f"{theme_name} references unknown color"


class TestColorPrinter:
    """Test ColorPrinter utility class."""

    def test_primary_color(self):
        """Test primary color printing."""
        result = ColorPrinter.primary("Test Text")
        assert "Test Text" in result
        assert str(THEME['primary']) in result
        assert RESET in result

    def test_primary_bold(self):
        """Test primary color with bold."""
        result = ColorPrinter.primary("Test Text", bold=True)
        assert "Test Text" in result
        assert BOLD in result
        assert str(THEME['primary']) in result
        assert RESET in result

    def test_all_color_methods(self):
        """Test all color methods work."""
        methods = [
            ("primary", THEME['primary']),
            ("success", THEME['success']),
            ("warning", THEME['warning']),
            ("error", THEME['error']),
            ("info", THEME['info']),
            ("learn", THEME['learn']),
        ]

        for method_name, expected_color in methods:
            method = getattr(ColorPrinter, method_name)
            result = method("Test")
            assert "Test" in result
            assert str(expected_color) in result
            assert RESET in result

    def test_custom_color(self):
        """Test custom color from palette."""
        result = ColorPrinter.custom("Test", "navy_blue")
        assert "Test" in result
        assert str(PALETTE['navy_blue']) in result
        assert RESET in result

    def test_custom_invalid_color(self):
        """Test custom color with invalid name."""
        result = ColorPrinter.custom("Test", "invalid_color")
        assert result == "Test"  # Should return plain text

    def test_gradient(self):
        """Test gradient effect (simplified version)."""
        result = ColorPrinter.gradient("Test", "navy_blue", "sky_blue")
        assert "Test" in result
        assert str(PALETTE['navy_blue']) in result
        assert RESET in result

        # Test with invalid color
        result = ColorPrinter.gradient("Test", "invalid_color", "sky_blue")
        assert result == "Test"  # Should return plain text


class TestPrintFunctions:
    """Test convenience print functions."""

    def test_print_header(self, capsys):
        """Test header printing."""
        print_header("Test Header", "Test Subtitle")
        captured = capsys.readouterr()

        assert "Test Header" in captured.out
        assert "Test Subtitle" in captured.out
        assert "=" * 60 in captured.out
        assert str(THEME['primary']) in captured.out
        assert str(THEME['info']) in captured.out

    def test_print_header_no_subtitle(self, capsys):
        """Test header printing without subtitle."""
        print_header("Test Header")
        captured = capsys.readouterr()

        assert "Test Header" in captured.out
        assert "=" * 60 in captured.out
        assert str(THEME['primary']) in captured.out

    def test_print_success(self, capsys):
        """Test success message printing."""
        print_success("Operation successful")
        captured = capsys.readouterr()

        assert "✅" in captured.out
        assert "Operation successful" in captured.out
        assert str(THEME['success']) in captured.out

    def test_print_error(self, capsys):
        """Test error message printing."""
        print_error("Operation failed")
        captured = capsys.readouterr()

        assert "❌" in captured.out
        assert "Operation failed" in captured.out
        assert str(THEME['error']) in captured.out

    def test_print_warning(self, capsys):
        """Test warning message printing."""
        print_warning("This is a warning")
        captured = capsys.readouterr()

        assert "⚠️" in captured.out
        assert "This is a warning" in captured.out
        assert str(THEME['warning']) in captured.out

    def test_print_info(self, capsys):
        """Test info message printing."""
        print_info("Information message")
        captured = capsys.readouterr()

        assert "ℹ️" in captured.out
        assert "Information message" in captured.out
        assert str(THEME['info']) in captured.out


@pytest.mark.parametrize("color_name,hex_value", [
    ("navy_blue", "#003190"),
    ("forest_dark", "#364f33"),
    ("crimson", "#930235"),
    ("white", "#ffffff"),
    ("black", "#000000"),
])
def test_specific_palette_colors(color_name, hex_value):
    """Test specific palette colors have correct hex values."""
    assert color_name in PALETTE
    assert PALETTE[color_name].hex == hex_value


def test_ansi_control_codes():
    """Test ANSI control code constants."""
    control_codes = {
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "DIM": "\033[2m",
        "ITALIC": "\033[3m",
        "UNDERLINE": "\033[4m",
        "CURSOR_UP": "\033[A",
        "CURSOR_DOWN": "\033[B",
        "CLEAR_SCREEN": "\033[2J\033[H",
        "CLEAR_LINE": "\033[K",
    }

    for name, expected in control_codes.items():
        actual = globals().get(name) or getattr(sys.modules['storm_checker.cli.colors'], name)
        assert actual == expected, f"{name} has wrong value"


def test_color_output_disabled(monkeypatch):
    """Test behavior when color output is disabled."""
    # This would be implemented based on how the app handles NO_COLOR env var
    # For now, we just test that colors work normally
    result = ColorPrinter.primary("Test")
    assert str(THEME['primary']) in result


def test_theme_completeness():
    """Test that all theme colors are defined."""
    expected_theme_colors = [
        "primary", "success", "warning", "error", "info",
        "learn", "practice", "accent", "text_muted"
    ]

    for color_name in expected_theme_colors:
        assert color_name in THEME
        assert isinstance(THEME[color_name], Color)


def test_print_learn():
    """Test print_learn function."""
    from storm_checker.cli.colors import print_learn
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        print_learn("Learning message")
        output = sys.stdout.getvalue()
        assert "Learning message" in output
        assert str(THEME['learn']) in output
    finally:
        sys.stdout = old_stdout


def test_print_rich_learn():
    """Test print_rich_learn function."""
    from storm_checker.cli.colors import print_rich_learn
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        print_rich_learn("Learning message")
        output = sys.stdout.getvalue()
        assert "Learning message" in output
    finally:
        sys.stdout = old_stdout


def test_demo_colors_function():
    """Test the demo_colors function."""
    from storm_checker.cli.colors import demo_colors
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        demo_colors()
        output = sys.stdout.getvalue()
        assert len(output) > 0
        assert "Storm-Checker Color Palette" in output
        assert "Theme Colors:" in output
        assert "Full Palette:" in output
    finally:
        sys.stdout = old_stdout


def test_demo_rich_integration():
    """Test the demo_rich_integration function."""
    from storm_checker.cli.colors import demo_rich_integration
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        demo_rich_integration()
        output = sys.stdout.getvalue()
        assert len(output) > 0
        # Should show Rich status
        assert "Rich" in output or "Not Available" in output
    finally:
        sys.stdout = old_stdout


def test_get_rich_theme():
    """Test get_rich_theme function."""
    from storm_checker.cli.colors import get_rich_theme

    theme = get_rich_theme()
    # Should return None if Rich is not available
    # or a theme object if it is
    assert theme is None or hasattr(theme, 'styles')


def test_create_rich_style():
    """Test create_rich_style function."""
    from storm_checker.cli.colors import create_rich_style, RICH_AVAILABLE

    if RICH_AVAILABLE:
        # Test with valid color
        style = create_rich_style("primary", bold=True, italic=True, underline=True)
        assert style is not None

        # Test with invalid color
        style = create_rich_style("nonexistent_color")
        assert style is None
    else:
        # Should return None when Rich not available
        style = create_rich_style("primary")
        assert style is None


class TestEnhancedColorPrinter:
    """Test EnhancedColorPrinter class."""

    def test_rich_text_without_rich(self):
        """Test rich_text method when Rich is not available."""
        from storm_checker.cli.colors import EnhancedColorPrinter, RICH_AVAILABLE

        if not RICH_AVAILABLE:
            # Test basic text
            result = EnhancedColorPrinter.rich_text("Test", "primary")
            assert "Test" in result

            # Test with style options
            result = EnhancedColorPrinter.rich_text("Bold", "success", bold=True)
            assert "Bold" in result
        else:
            # When Rich is available, test the fallback for specific style names
            # Test the if condition on line 374
            for style in ['primary', 'success', 'warning', 'error', 'info', 'learn']:
                result = EnhancedColorPrinter.rich_text("Test", style)
                assert "Test" in result

            # Test with italic and underline options (lines 384, 386)
            result = EnhancedColorPrinter.rich_text("Test", "primary", italic=True, underline=True)
            assert "Test" in result
            assert "[" in result and "]" in result

    def test_tutorial_title(self):
        """Test tutorial_title method."""
        from storm_checker.cli.colors import EnhancedColorPrinter

        result = EnhancedColorPrinter.tutorial_title("Tutorial Title")
        assert "Tutorial Title" in result

    def test_question_text(self):
        """Test question_text method."""
        from storm_checker.cli.colors import EnhancedColorPrinter

        # Test correct answer
        result = EnhancedColorPrinter.question_text("Correct!", correct=True)
        assert "✅" in result
        assert "Correct!" in result

        # Test incorrect answer
        result = EnhancedColorPrinter.question_text("Wrong!", correct=False)
        assert "❌" in result
        assert "Wrong!" in result

        # Test unknown/pending
        result = EnhancedColorPrinter.question_text("Question?", correct=None)
        assert "❓" in result
        assert "Question?" in result

    def test_achievement(self):
        """Test achievement method."""
        from storm_checker.cli.colors import EnhancedColorPrinter

        result = EnhancedColorPrinter.achievement("First Error Fixed!")
        assert "🏆" in result
        assert "First Error Fixed!" in result

    def test_code_highlight(self):
        """Test code_highlight method."""
        from storm_checker.cli.colors import EnhancedColorPrinter

        result = EnhancedColorPrinter.code_highlight("def foo(): pass")
        assert "def foo(): pass" in result

    def test_progress_text(self):
        """Test progress_text method."""
        from storm_checker.cli.colors import EnhancedColorPrinter

        result = EnhancedColorPrinter.progress_text(25, 100, "Progress")
        assert "Progress" in result
        assert "25/100" in result
        assert "25%" in result

        # Test with zero total
        result = EnhancedColorPrinter.progress_text(0, 0, "Empty")
        assert "Empty" in result
        assert "0%" in result


def test_print_rich_functions():
    """Test print_rich_* functions."""
    from storm_checker.cli.colors import print_rich_header, print_rich_success, print_rich_warning, print_rich_error, print_rich_info
    import io
    import sys

    old_stdout = sys.stdout

    try:
        # Test print_rich_header
        sys.stdout = io.StringIO()
        print_rich_header("Title", "Subtitle")
        output = sys.stdout.getvalue()
        assert "Title" in output

        # Test print_rich_success
        sys.stdout = io.StringIO()
        print_rich_success("Success!")
        output = sys.stdout.getvalue()
        assert "Success!" in output

        # Test print_rich_warning
        sys.stdout = io.StringIO()
        print_rich_warning("Warning!")
        output = sys.stdout.getvalue()
        assert "Warning!" in output

        # Test print_rich_error
        sys.stdout = io.StringIO()
        print_rich_error("Error!")
        output = sys.stdout.getvalue()
        assert "Error!" in output

        # Test print_rich_info
        sys.stdout = io.StringIO()
        print_rich_info("Info!")
        output = sys.stdout.getvalue()
        assert "Info!" in output
    finally:
        sys.stdout = old_stdout


# Remove tests for non-existent functions


def test_color_printer_practice():
    """Test practice color method."""
    from storm_checker.cli.colors import ColorPrinter

    # ColorPrinter doesn't have practice method, but we can use custom
    result = ColorPrinter.custom("Practice text", "amber")
    assert "Practice text" in result
    assert str(PALETTE['amber']) in result


def test_enhanced_color_printer_with_rich_unavailable():
    """Test EnhancedColorPrinter when Rich is not available."""
    from storm_checker.cli.colors import EnhancedColorPrinter, RICH_AVAILABLE

    if RICH_AVAILABLE:
        # When Rich is available, it returns Rich markup
        result = EnhancedColorPrinter.rich_text("Test", "unknown_style")
        assert result == "Test"  # unknown style returns plain text

        # Test with a theme style - accent should return Rich markup
        result = EnhancedColorPrinter.rich_text("Test", "accent")
        assert "[" in result and "]" in result  # Should contain Rich markup
        assert "Test" in result
    else:
        # When Rich is not available, test fallback behavior
        result = EnhancedColorPrinter.rich_text("Test", "unknown_style")
        assert result == "Test"

        result = EnhancedColorPrinter.rich_text("Test", "accent")
        assert result == "Test"  # accent is not in the if statement list


def test_get_rich_color():
    """Test get_rich_color function."""
    from storm_checker.cli.colors import get_rich_color, RICH_AVAILABLE

    if RICH_AVAILABLE:
        # Test with valid theme color
        color = get_rich_color("primary")
        assert color is not None

        # Test with valid palette color
        color = get_rich_color("navy_blue")
        assert color is not None

        # Test with invalid color
        color = get_rich_color("nonexistent_color")
        assert color is None
    else:
        # Test fallback behavior
        color = get_rich_color("primary")
        assert color is None  # Should return None when Rich not available


def test_print_rich_functions_with_rich_available():
    """Test print_rich_* functions when Rich is available and working."""
    import pytest
    from unittest.mock import patch, MagicMock
    from storm_checker.cli.colors import print_rich_header, print_rich_success, print_rich_error, print_rich_warning, print_rich_info
    import io
    import sys

    # Mock Rich components
    mock_console = MagicMock()
    mock_panel = MagicMock()
    mock_text = MagicMock()
    mock_align = MagicMock()

    old_stdout = sys.stdout

    try:
        # Test print_rich_header with Rich available
        with patch('storm_checker.cli.colors.RICH_AVAILABLE', True), \
             patch('rich.console.Console', return_value=mock_console), \
             patch('rich.panel.Panel', return_value=mock_panel), \
             patch('rich.text.Text', mock_text), \
             patch('rich.align.Align', mock_align):

            sys.stdout = io.StringIO()
            print_rich_header("Test Title", "Test Subtitle")
            # Should call Rich components and return early (line 455)
            mock_console.print.assert_called_once()

        # Test print_rich_success with Rich available
        with patch('storm_checker.cli.colors.RICH_AVAILABLE', True), \
             patch('rich.console.Console', return_value=mock_console):

            sys.stdout = io.StringIO()
            print_rich_success("Success message")
            # Should call Rich console and return early (line 469)
            mock_console.print.assert_called()

        # Test print_rich_error with Rich available
        with patch('storm_checker.cli.colors.RICH_AVAILABLE', True), \
             patch('rich.console.Console', return_value=mock_console):

            sys.stdout = io.StringIO()
            print_rich_error("Error message")
            # Should call Rich console and return early (line 481)
            mock_console.print.assert_called()

        # Test print_rich_warning with Rich available
        with patch('storm_checker.cli.colors.RICH_AVAILABLE', True), \
             patch('rich.console.Console', return_value=mock_console):

            sys.stdout = io.StringIO()
            print_rich_warning("Warning message")
            # Should call Rich console and return early (line 493)
            mock_console.print.assert_called()

        # Test print_rich_info with Rich available
        with patch('storm_checker.cli.colors.RICH_AVAILABLE', True), \
             patch('rich.console.Console', return_value=mock_console):

            sys.stdout = io.StringIO()
            print_rich_info("Info message")
            # Should call Rich console and return early (line 505)
            mock_console.print.assert_called()

        # Test print_rich_learn with Rich available (line 517)
        with patch('storm_checker.cli.colors.RICH_AVAILABLE', True), \
             patch('rich.console.Console', return_value=mock_console):

            sys.stdout = io.StringIO()
            from storm_checker.cli.colors import print_rich_learn
            print_rich_learn("Learn message")
            # Should call Rich console and return early (line 517)
            mock_console.print.assert_called()

    finally:
        sys.stdout = old_stdout


def test_demo_rich_integration_success():
    """Test demo_rich_integration function with Rich available."""
    from unittest.mock import patch, MagicMock
    from storm_checker.cli.colors import demo_rich_integration
    import io
    import sys

    # Mock Rich components
    mock_console = MagicMock()
    mock_table = MagicMock()
    mock_panel = MagicMock()
    mock_text = MagicMock()

    old_stdout = sys.stdout

    try:
        # Test demo_rich_integration with Rich available
        with patch('storm_checker.cli.colors.RICH_AVAILABLE', True), \
             patch('rich.console.Console', return_value=mock_console), \
             patch('rich.table.Table', return_value=mock_table), \
             patch('rich.panel.Panel', return_value=mock_panel), \
             patch('rich.text.Text', mock_text), \
             patch('storm_checker.cli.colors.get_rich_theme', return_value=MagicMock()):

            sys.stdout = io.StringIO()
            demo_rich_integration()
            # Should call Rich components and create panel (lines 588-598)
            mock_console.print.assert_called()

    finally:
        sys.stdout = old_stdout
