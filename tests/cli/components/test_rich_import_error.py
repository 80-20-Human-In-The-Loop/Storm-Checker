#!/usr/bin/env python3
"""
Test Rich Import Error Handling
================================
Separate test file to ensure clean import testing for lines 29-31.
This test must run in isolation to properly test import error handling.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch, Mock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def test_rich_import_error_handling():
    """Test that import errors are handled gracefully (lines 29-31)."""
    
    # Remove any existing imports to ensure clean slate
    modules_to_remove = [
        'storm_checker.cli.components.rich_terminal',
        'rich', 'rich.console', 'rich.text', 'rich.panel',
        'rich.table', 'rich.progress', 'rich.layout', 'rich.live',
        'rich.markdown', 'rich.syntax', 'rich.rule', 'rich.prompt',
        'rich.align', 'rich.padding', 'rich.columns', 'rich.tree'
    ]
    
    # Save original modules
    saved_modules = {}
    for module in modules_to_remove:
        if module in sys.modules:
            saved_modules[module] = sys.modules[module]
            del sys.modules[module]
    
    try:
        # Mock the import to raise ImportError for rich modules
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__
        
        def mock_import(name, *args, **kwargs):
            # Raise ImportError for any rich module
            if 'rich' in name and not 'storm_checker' in name:
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', mock_import):
            # This import should trigger the except ImportError block (lines 29-31)
            import storm_checker.cli.components.rich_terminal as rt
            
            # Verify that the ImportError was handled correctly
            assert rt.RICH_AVAILABLE is False
            assert rt.Console is None
            
            # Verify that RichTerminal still works without Rich
            with patch.object(rt, 'BufferedRenderer') as mock_br:
                mock_instance = Mock()
                mock_br.return_value = mock_instance
                
                terminal = rt.RichTerminal(use_rich=True)
                assert terminal.use_rich is False  # Should be False since RICH_AVAILABLE is False
                assert terminal.console is None
                
    finally:
        # Clean up - remove the module we imported
        if 'storm_checker.cli.components.rich_terminal' in sys.modules:
            del sys.modules['storm_checker.cli.components.rich_terminal']
            
        # Restore original modules
        for module, original in saved_modules.items():
            sys.modules[module] = original


if __name__ == "__main__":
    # Run the test directly
    test_rich_import_error_handling()
    print("✅ Import error handling test passed!")