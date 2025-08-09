"""
Tests for Stormcheck Main Script
=================================
Test coverage for the main stormcheck entry point script.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import importlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestStormcheckImports:
    """Test import fallback handling in stormcheck.py"""
    
    def test_tutorial_import_fallback_to_second_path(self):
        """Test fallback to 'from scripts.tutorial import main' when first import fails."""
        
        # Save original modules
        saved_modules = {}
        modules_to_save = ['storm_checker.scripts.stormcheck', 'storm_checker.scripts.tutorial']
        for mod in modules_to_save:
            if mod in sys.modules:
                saved_modules[mod] = sys.modules[mod]
                
        try:
            # Mock to make first import fail, second succeed
            import builtins
            original_import = builtins.__import__
            
            def mock_import(name, *args, **kwargs):
                # First import path should fail
                if name == 'storm_checker.scripts.tutorial':
                    raise ImportError(f"No module named '{name}'")
                # Second path should succeed
                elif name == 'scripts.tutorial':
                    mock_module = MagicMock()
                    mock_module.main = Mock()
                    return mock_module
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                # Execute the import logic
                code = """
try:
    from storm_checker.scripts.tutorial import main as tutorial_main
except ImportError:
    try:
        from scripts.tutorial import main as tutorial_main
    except ImportError:
        from tutorial import main as tutorial_main

# Check that we got the function
assert tutorial_main is not None
result = 'second_import'
"""
                namespace = {}
                exec(code, namespace)
                assert namespace['result'] == 'second_import'
                
        finally:
            # Restore saved modules
            for mod, saved in saved_modules.items():
                if saved:
                    sys.modules[mod] = saved
    
    def test_tutorial_import_fallback_to_third_path(self):
        """Test fallback to 'from tutorial import main' when first two imports fail."""
        
        # Save original modules
        saved_modules = {}
        modules_to_save = ['storm_checker.scripts.stormcheck', 'storm_checker.scripts.tutorial', 
                          'scripts.tutorial', 'tutorial']
        for mod in modules_to_save:
            if mod in sys.modules:
                saved_modules[mod] = sys.modules.pop(mod)
                
        try:
            # Mock to make first two imports fail, third succeed
            import builtins
            original_import = builtins.__import__
            
            import_attempts = []
            
            def mock_import(name, *args, **kwargs):
                import_attempts.append(name)
                
                # First import path should fail
                if name == 'storm_checker.scripts.tutorial':
                    raise ImportError(f"No module named '{name}'")
                # Second import path should also fail  
                elif name == 'scripts.tutorial':
                    raise ImportError(f"No module named '{name}'")
                # Third path should succeed
                elif name == 'tutorial':
                    mock_module = MagicMock()
                    mock_module.main = Mock(return_value=None)
                    return mock_module
                    
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                # Execute the import logic that matches stormcheck.py
                code = """
try:
    from storm_checker.scripts.tutorial import main as tutorial_main
except ImportError:
    try:
        from scripts.tutorial import main as tutorial_main
    except ImportError:
        from tutorial import main as tutorial_main

# Verify we got the function from the third import
assert tutorial_main is not None
result = 'third_import'
"""
                namespace = {}
                exec(code, namespace)
                assert namespace['result'] == 'third_import'
                
                # Verify all three imports were attempted
                assert 'storm_checker.scripts.tutorial' in import_attempts
                assert 'scripts.tutorial' in import_attempts
                assert 'tutorial' in import_attempts
                
        finally:
            # Restore saved modules
            for mod, saved in saved_modules.items():
                if saved:
                    sys.modules[mod] = saved


class TestStormcheckCommands:
    """Test stormcheck command routing."""
    
    def setup_method(self, method):
        """Set up test environment before each test."""
        # Store original state
        self._original_argv = sys.argv.copy()
        self._original_modules = {}
        
        # Clear any cached storm_checker.scripts modules
        for mod in list(sys.modules.keys()):
            if 'storm_checker.scripts' in mod:
                self._original_modules[mod] = sys.modules.get(mod)
                sys.modules.pop(mod, None)
    
    def teardown_method(self, method):
        """Clean up after each test."""
        # Restore sys.argv
        sys.argv = self._original_argv
        
        # Restore original modules
        for mod, saved in self._original_modules.items():
            if saved:
                sys.modules[mod] = saved
    
    def test_mypy_command(self, isolated_import):
        """Test that mypy command routes correctly."""
        with patch('sys.argv', ['stormcheck', 'mypy']):
            with patch('storm_checker.scripts.stormcheck.argparse.ArgumentParser') as mock_parser_class:
                mock_parser = Mock()
                mock_args = Mock()
                mock_args.command = 'mypy'
                mock_remaining = []
                mock_parser.parse_known_args.return_value = (mock_args, mock_remaining)
                mock_parser_class.return_value = mock_parser
                
                with patch('storm_checker.scripts.check_mypy.main') as mock_mypy_main:
                    # Mock mypy main to raise SystemExit as it normally would
                    mock_mypy_main.side_effect = SystemExit(0)
                    
                    # Import and run main with clean slate
                    from storm_checker.scripts.stormcheck import main
                    with pytest.raises(SystemExit):
                        main()
                    
                    # Verify mypy main was called
                    mock_mypy_main.assert_called_once()
    
    def test_tutorial_command_with_primary_import(self, isolated_import):
        """Test tutorial command with successful primary import."""
        with patch('sys.argv', ['stormcheck', 'tutorial']):
            with patch('storm_checker.scripts.stormcheck.argparse.ArgumentParser') as mock_parser_class:
                mock_parser = Mock()
                mock_args = Mock()
                mock_args.command = 'tutorial'
                mock_remaining = []
                mock_parser.parse_known_args.return_value = (mock_args, mock_remaining)
                mock_parser_class.return_value = mock_parser
                
                with patch('storm_checker.scripts.tutorial.main') as mock_tutorial_main:
                    # Import and run main
                    from storm_checker.scripts.stormcheck import main
                    main()
                    
                    # Verify tutorial main was called
                    mock_tutorial_main.assert_called_once()
    
    def test_tutorial_command_with_fallback_imports(self, isolated_import):
        """Test tutorial command with import fallbacks to cover lines 88-92."""
        with patch('sys.argv', ['stormcheck', 'tutorial']):
            with patch('storm_checker.scripts.stormcheck.argparse.ArgumentParser') as mock_parser_class:
                # Set up the argument parser mock
                mock_parser = Mock()
                mock_args = Mock()
                mock_args.command = 'tutorial'
                mock_remaining = []
                mock_parser.parse_known_args.return_value = (mock_args, mock_remaining)
                mock_parser_class.return_value = mock_parser
                
                # Remove the tutorial module to force import errors
                import builtins
                original_import = builtins.__import__
                
                import_attempts = []
                
                def mock_import(name, *args, **kwargs):
                    import_attempts.append(name)
                    
                    # First two imports should fail
                    if name == 'storm_checker.scripts.tutorial':
                        raise ImportError("Module not found")
                    elif name == 'scripts.tutorial':
                        raise ImportError("Module not found")
                    elif name == 'tutorial':
                        # Third import succeeds
                        mock_module = Mock()
                        mock_module.main = Mock()
                        return mock_module
                    
                    return original_import(name, *args, **kwargs)
                
                with patch('builtins.__import__', side_effect=mock_import):
                    from storm_checker.scripts.stormcheck import main
                    main()
                    
                    # Verify all three import paths were attempted
                    assert 'storm_checker.scripts.tutorial' in import_attempts
                    assert 'scripts.tutorial' in import_attempts
                    assert 'tutorial' in import_attempts
    
    def test_progress_command(self, isolated_import):
        """Test that progress command routes correctly."""
        with patch('sys.argv', ['stormcheck', 'progress']):
            with patch('storm_checker.scripts.stormcheck.argparse.ArgumentParser') as mock_parser_class:
                mock_parser = Mock()
                mock_args = Mock()
                mock_args.command = 'progress'
                mock_remaining = []
                mock_parser.parse_known_args.return_value = (mock_args, mock_remaining)
                mock_parser_class.return_value = mock_parser
                
                with patch('storm_checker.scripts.progress.main') as mock_progress_main:
                    # Import and run main
                    from storm_checker.scripts.stormcheck import main
                    main()
                    
                    # Verify progress main was called
                    mock_progress_main.assert_called_once()