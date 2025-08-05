"""
Additional edge case tests for colors.py
========================================
Test exception handling and edge cases.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_rich_import_error():
    """Test handling when Rich import fails."""
    # Test the import error handling (lines 279-283)
    import sys
    import importlib
    
    # Save original rich module if it exists
    rich_module = sys.modules.get('rich')
    rich_theme = sys.modules.get('rich.theme')
    rich_color = sys.modules.get('rich.color')
    rich_style = sys.modules.get('rich.style')
    
    try:
        # Remove rich modules to simulate import failure
        for mod in ['rich', 'rich.theme', 'rich.color', 'rich.style']:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # Mock the import to fail
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'rich' or name.startswith('rich.'):
                raise ImportError("Rich not available")
            return original_import(name, *args, **kwargs)
        
        builtins.__import__ = mock_import
        
        # Now reload the colors module to test import error handling
        if 'cli.colors' in sys.modules:
            del sys.modules['cli.colors']
        
        import cli.colors
        
        # Should have handled the import error gracefully
        assert cli.colors.RICH_AVAILABLE == False
        assert cli.colors.RichTheme is None
        assert cli.colors.RichColor is None
        assert cli.colors.RichStyle is None
        
    finally:
        # Restore import
        builtins.__import__ = original_import
        
        # Restore rich modules
        if rich_module:
            sys.modules['rich'] = rich_module
        if rich_theme:
            sys.modules['rich.theme'] = rich_theme
        if rich_color:
            sys.modules['rich.color'] = rich_color
        if rich_style:
            sys.modules['rich.style'] = rich_style


def test_get_rich_theme_no_rich():
    """Test get_rich_theme when Rich is not available."""
    with patch('storm_checker.cli.colors.RICH_AVAILABLE', False):
        from cli.colors import get_rich_theme
        theme = get_rich_theme()
        assert theme is None


def test_get_rich_color_no_rich():
    """Test get_rich_color when Rich is not available."""
    with patch('storm_checker.cli.colors.RICH_AVAILABLE', False):
        from cli.colors import get_rich_color
        # Should return None when Rich not available (line 334)
        color = get_rich_color("primary")
        assert color is None


def test_create_rich_style_no_rich():
    """Test create_rich_style when Rich is not available."""  
    with patch('storm_checker.cli.colors.RICH_AVAILABLE', False):
        from cli.colors import create_rich_style
        # Should return None when Rich not available (line 352)
        style = create_rich_style("primary", bold=True)
        assert style is None


def test_print_rich_header_exception():
    """Test print_rich_header exception handling."""
    from cli.colors import RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        # Make Panel creation fail to test line 455
        with patch('rich.panel.Panel', side_effect=Exception("Panel error")):
            from cli.colors import print_rich_header
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                print_rich_header("Test", "Subtitle")
                output = sys.stdout.getvalue()
                assert "Test" in output  # Should fallback to regular print_header
                assert "=" in output  # Should have divider from regular header
            finally:
                sys.stdout = old_stdout


def test_print_rich_success_exception():
    """Test print_rich_success exception handling."""
    from cli.colors import RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        with patch('rich.console.Console', side_effect=Exception("Console error")):
            from cli.colors import print_rich_success
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                print_rich_success("Success message")
                output = sys.stdout.getvalue()
                assert "✅" in output
                assert "Success message" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_error_exception():
    """Test print_rich_error exception handling."""
    from cli.colors import RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        with patch('rich.console.Console', side_effect=Exception("Console error")):
            from cli.colors import print_rich_error
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                print_rich_error("Error message")
                output = sys.stdout.getvalue()
                assert "❌" in output
                assert "Error message" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_warning_exception():
    """Test print_rich_warning exception handling."""
    from cli.colors import RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        with patch('rich.console.Console', side_effect=Exception("Console error")):
            from cli.colors import print_rich_warning
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                print_rich_warning("Warning message")
                output = sys.stdout.getvalue()
                assert "⚠️" in output
                assert "Warning message" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_info_exception():
    """Test print_rich_info exception handling."""
    from cli.colors import RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        with patch('rich.console.Console', side_effect=Exception("Console error")):
            from cli.colors import print_rich_info
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                print_rich_info("Info message")
                output = sys.stdout.getvalue()
                assert "ℹ️" in output
                assert "Info message" in output
            finally:
                sys.stdout = old_stdout


def test_print_rich_learn_exception():
    """Test print_rich_learn exception handling."""
    from cli.colors import RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        with patch('rich.console.Console', side_effect=Exception("Console error")):
            from cli.colors import print_rich_learn
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                print_rich_learn("Learn message")
                output = sys.stdout.getvalue()
                assert "📚" in output
                assert "Learn message" in output
            finally:
                sys.stdout = old_stdout


def test_demo_rich_integration_no_rich():
    """Test demo_rich_integration when Rich is not available."""
    with patch('storm_checker.cli.colors.RICH_AVAILABLE', False):
        from cli.colors import demo_rich_integration
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            demo_rich_integration()
            output = sys.stdout.getvalue()
            assert "Rich library not available" in output
        finally:
            sys.stdout = old_stdout


def test_demo_rich_integration_exception():
    """Test demo_rich_integration exception handling."""
    from cli.colors import RICH_AVAILABLE, demo_rich_integration
    
    if RICH_AVAILABLE:
        with patch('rich.console.Console') as MockConsole:
            # Make Console creation fail
            MockConsole.side_effect = Exception("Console creation failed")
            
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                demo_rich_integration()
                output = sys.stdout.getvalue()
                # Should fallback to demo_colors
                assert len(output) > 0
                assert "Storm-Checker Color Palette" in output  # demo_colors output
            finally:
                sys.stdout = old_stdout


def test_enhanced_color_printer_rich_markup_edge_cases():
    """Test EnhancedColorPrinter rich_text edge cases."""
    from cli.colors import EnhancedColorPrinter, RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        # Test with no color found (line 397)
        with patch('storm_checker.cli.colors.get_rich_color', return_value=None):
            result = EnhancedColorPrinter.rich_text("Test", "invalid")
            assert result == "Test"  # Should return plain text


def test_enhanced_color_printer_fallback_no_rich():
    """Test EnhancedColorPrinter fallback when RICH_AVAILABLE is False."""
    # Test lines 374-376
    with patch('storm_checker.cli.colors.RICH_AVAILABLE', False):
        from cli.colors import EnhancedColorPrinter
        
        # Test with style in the list
        for style in ['primary', 'success', 'warning', 'error', 'info', 'learn']:
            result = EnhancedColorPrinter.rich_text("Test", style)
            assert "Test" in result
            
        # Test with style not in the list
        result = EnhancedColorPrinter.rich_text("Test", "unknown")
        assert result == "Test"


def test_rich_theme_panel_creation():
    """Test Panel creation in print_rich_header."""
    from cli.colors import RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        # Test successful panel creation with complex content
        from cli.colors import print_rich_header
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # This should exercise the Panel creation code
            print_rich_header("Title", "Subtitle")
            output = sys.stdout.getvalue()
            # Should have created output
            assert len(output) > 0
        finally:
            sys.stdout = old_stdout


def test_demo_rich_integration_panel():
    """Test demo_rich_integration Panel creation."""
    from cli.colors import RICH_AVAILABLE
    
    if RICH_AVAILABLE:
        from cli.colors import demo_rich_integration
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # This should exercise line 588 - Panel creation
            demo_rich_integration()
            output = sys.stdout.getvalue()
            # Should have created rich output
            assert len(output) > 0
            assert "Rich Integration Demo" in output or "Color Palette" in output
        finally:
            sys.stdout = old_stdout


def test_ansi_control_codes_edge_case():
    """Test ANSI control codes that might not be in globals."""
    # Test line 235 - when a control code is not in globals
    import cli.colors
    
    # All control codes should be accessible
    control_codes = [
        "RESET", "BOLD", "DIM", "ITALIC", "UNDERLINE",
        "CURSOR_UP", "CURSOR_DOWN", "CLEAR_SCREEN", "CLEAR_LINE"
    ]
    
    for code in control_codes:
        assert hasattr(cli.colors, code)
        value = getattr(cli.colors, code)
        assert isinstance(value, str)
        assert value.startswith("\033")  # ANSI escape sequence


def test_color_printer_fallback_paths():
    """Test ColorPrinter methods to ensure fallback coverage."""
    from cli.colors import ColorPrinter, RICH_AVAILABLE
    
    # Temporarily mock RICH_AVAILABLE to test fallback
    original_rich = RICH_AVAILABLE
    
    try:
        # Test when style name is not in the specific list (line 374-376)
        import cli.colors
        cli.colors.RICH_AVAILABLE = False
        
        from cli.colors import EnhancedColorPrinter
        # Now test the fallback path
        result = EnhancedColorPrinter.rich_text("Test", "primary")
        assert "Test" in result
        
        result = EnhancedColorPrinter.rich_text("Test", "unknown")
        assert result == "Test"
    finally:
        cli.colors.RICH_AVAILABLE = original_rich