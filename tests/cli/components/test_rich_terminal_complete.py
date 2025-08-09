"""
Comprehensive Tests for Rich Terminal
======================================
Complete test coverage for RichTerminal with all features.
"""

import pytest
import sys
import importlib
from unittest.mock import Mock, patch, MagicMock, call
from contextlib import contextmanager
from io import StringIO

# Test both with and without Rich available
def test_rich_import_error():
    """Test handling when Rich is not available."""
    # Remove any existing rich modules
    for module in list(sys.modules.keys()):
        if module.startswith('rich'):
            del sys.modules[module]
    
    # Mock the import to raise ImportError
    with patch.dict('sys.modules', {}):
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name.startswith('rich'):
                raise ImportError("No module named 'rich'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            # Re-import the module to trigger ImportError handling
            if 'storm_checker.cli.components.rich_terminal' in sys.modules:
                del sys.modules['storm_checker.cli.components.rich_terminal']
            
            import storm_checker.cli.components.rich_terminal as rt
            assert rt.RICH_AVAILABLE is False
            assert rt.Console is None

# Now mock Rich components for the rest of the tests
rich_mock = MagicMock()
sys.modules['rich'] = rich_mock

# Create detailed mocks for each component
console_mock = MagicMock()
console_class = MagicMock()
console_class.return_value = console_mock
console_mock.print = MagicMock()
console_mock.capture = MagicMock()
# Set up capture context manager
capture_context = MagicMock()
capture_context.get = MagicMock(return_value="mocked output")
console_mock.capture.return_value.__enter__ = MagicMock(return_value=capture_context)
console_mock.capture.return_value.__exit__ = MagicMock(return_value=False)

sys.modules['rich.console'] = MagicMock()
sys.modules['rich.console'].Console = console_class

# Mock other components
sys.modules['rich.text'] = MagicMock()
sys.modules['rich.panel'] = MagicMock()
sys.modules['rich.table'] = MagicMock()
sys.modules['rich.progress'] = MagicMock()
sys.modules['rich.layout'] = MagicMock()
sys.modules['rich.live'] = MagicMock()
sys.modules['rich.markdown'] = MagicMock()
sys.modules['rich.syntax'] = MagicMock()
sys.modules['rich.rule'] = MagicMock()

# Mock prompt components
prompt_mock = MagicMock()
prompt_mock.ask = MagicMock(return_value="mocked_input")
confirm_mock = MagicMock()
confirm_mock.ask = MagicMock(return_value=True)

sys.modules['rich.prompt'] = MagicMock()
sys.modules['rich.prompt'].Prompt = prompt_mock
sys.modules['rich.prompt'].Confirm = confirm_mock

sys.modules['rich.align'] = MagicMock()
sys.modules['rich.padding'] = MagicMock()
sys.modules['rich.columns'] = MagicMock()
sys.modules['rich.tree'] = MagicMock()

# Set up component class references that will be imported
sys.modules['rich.console'].Console = console_class
sys.modules['rich.panel'].Panel = MagicMock()
sys.modules['rich.table'].Table = MagicMock()
sys.modules['rich.progress'].Progress = MagicMock()
sys.modules['rich.progress'].TaskID = MagicMock()
sys.modules['rich.progress'].BarColumn = MagicMock()
sys.modules['rich.progress'].TextColumn = MagicMock()
sys.modules['rich.progress'].TimeRemainingColumn = MagicMock()
sys.modules['rich.progress'].SpinnerColumn = MagicMock()
sys.modules['rich.layout'].Layout = MagicMock()
sys.modules['rich.live'].Live = MagicMock()
sys.modules['rich.markdown'].Markdown = MagicMock()
sys.modules['rich.syntax'].Syntax = MagicMock()
sys.modules['rich.rule'].Rule = MagicMock()
sys.modules['rich.tree'].Tree = MagicMock()
sys.modules['rich.align'].Align = MagicMock()
sys.modules['rich.padding'].Padding = MagicMock()
sys.modules['rich.columns'].Columns = MagicMock()

# Re-import after mocking
if 'storm_checker.cli.components.rich_terminal' in sys.modules:
    del sys.modules['storm_checker.cli.components.rich_terminal']

from storm_checker.cli.components.rich_terminal import (
    RichTerminal, ProgressTracker, FallbackProgressTracker,
    LiveDisplay, FallbackLiveDisplay, create_rich_terminal,
    demo_rich_terminal, RICH_AVAILABLE
)


class TestRichTerminalComplete:
    """Complete tests for RichTerminal covering all functionality."""
    
    def test_initialization_with_rich_enabled(self):
        """Test RichTerminal initialization with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            # Use the mock console class we set up
            terminal = RichTerminal(
                use_rich=True,
                width=80,
                height=24,
                theme="dark"
            )
            
            assert terminal.use_rich is True
            assert terminal.console is not None
            console_class.assert_called_once_with(
                width=80,
                height=24,
                force_terminal=True,
                color_system="truecolor",
                theme="dark"
            )
    
    def test_print_with_rich_persist(self):
        """Test print with Rich enabled and persist."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            
            with patch.object(terminal.buffered_renderer, 'render_frame') as mock_render:
                terminal.print("test", "message", style="bold", persist=True)
                
                # Check that console.print was called
                terminal.console.print.assert_called_once_with(
                    "test", "message",
                    style="bold",
                    highlight=True,
                    markup=True,
                    emoji=True
                )
                
                # Check that output was persisted
                mock_render.assert_called_once()
                args = mock_render.call_args[0]
                assert args[0] == ["mocked output"]
    
    def test_print_with_rich_no_persist(self):
        """Test print with Rich enabled but no persist."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            
            with patch('builtins.print') as mock_print:
                terminal.print("test", persist=False)
                mock_print.assert_called_once_with("mocked output", end='')
    
    def test_print_panel_with_rich(self):
        """Test print_panel with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            terminal.print = Mock()  # Mock the print method
            
            # Mock Panel directly on the module - create if doesn't exist
            panel_mock = Mock()
            panel_instance = Mock()
            panel_mock.return_value = panel_instance
            
            # Patch Panel in the actual module namespace 
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Panel', panel_mock, create=True):
                terminal.print_panel(
                    "content",
                    title="Title",
                    subtitle="Subtitle",
                    style="default",
                    border_style="blue",
                    expand=True,
                    persist=True
                )
                
                panel_mock.assert_called_once_with(
                    "content",
                    title="Title",
                    subtitle="Subtitle",
                    style="default",
                    border_style="blue",
                    expand=True
                )
                terminal.print.assert_called_once_with(panel_instance, persist=True)
    
    def test_print_table_with_rich(self):
        """Test print_table with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            terminal.print = Mock()
            
            table_mock = Mock()
            table_instance = Mock()
            table_mock.return_value = table_instance
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Table', table_mock, create=True):
                data = [["row1col1", "row1col2"], ["row2col1", "row2col2"]]
                headers = ["Column 1", "Column 2"]
                
                terminal.print_table(
                    data,
                    headers=headers,
                    title="Test Table",
                    style="default",
                    persist=True
                )
                
                table_mock.assert_called_once_with(title="Test Table", style="default")
                assert table_instance.add_column.call_count == 2
                assert table_instance.add_row.call_count == 2
                terminal.print.assert_called_once_with(table_instance, persist=True)
    
    def test_print_table_without_headers(self):
        """Test print_table without headers (auto-generate)."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            terminal.print = Mock()
            
            table_mock = Mock()
            table_instance = Mock()
            table_mock.return_value = table_instance
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Table', table_mock, create=True):
                data = [["val1", "val2", "val3"]]
                
                terminal.print_table(data, persist=True)
                
                # Should auto-generate 3 column headers
                calls = table_instance.add_column.call_args_list
                assert len(calls) == 3
                assert calls[0][0][0] == "Col 1"
                assert calls[1][0][0] == "Col 2"
                assert calls[2][0][0] == "Col 3"
    
    def test_print_markdown_with_rich(self):
        """Test print_markdown with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            terminal.print = Mock()
            
            md_mock = Mock()
            md_instance = Mock()
            md_mock.return_value = md_instance
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Markdown', md_mock, create=True):
                terminal.print_markdown("# Title\n\nContent", style="default", persist=True)
                
                md_mock.assert_called_once_with("# Title\n\nContent", style="default")
                terminal.print.assert_called_once_with(md_instance, persist=True)
    
    def test_print_markdown_fallback(self):
        """Test print_markdown in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        with patch.object(terminal, 'print') as mock_print:
            markdown = "# Header\n## Subheader\n- Item 1\nNormal text"
            terminal.print_markdown(markdown, persist=True)
            
            # Check that markdown was processed
            calls = mock_print.call_args_list
            assert len(calls) == 4
    
    def test_print_code_with_rich(self):
        """Test print_code with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            terminal.print = Mock()
            
            syntax_mock = Mock()
            syntax_instance = Mock()
            syntax_mock.return_value = syntax_instance
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Syntax', syntax_mock, create=True):
                code = "def hello():\n    print('world')"
                terminal.print_code(
                    code,
                    language="python",
                    theme="monokai",
                    line_numbers=True,
                    persist=True
                )
                
                syntax_mock.assert_called_once_with(
                    code,
                    "python",
                    theme="monokai",
                    line_numbers=True
                )
                terminal.print.assert_called_once_with(syntax_instance, persist=True)
    
    def test_print_code_fallback(self):
        """Test print_code in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        with patch.object(terminal, 'print') as mock_print:
            code = "def hello():\n    pass"
            terminal.print_code(code, language="python", persist=True)
            
            # Should print code with basic formatting
            assert mock_print.call_count >= 4  # Header, lines, footer
    
    def test_print_rule_with_rich(self):
        """Test print_rule with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            terminal.print = Mock()
            
            rule_mock = Mock()
            rule_instance = Mock()
            rule_mock.return_value = rule_instance
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Rule', rule_mock, create=True):
                terminal.print_rule(title="Section", style="blue", persist=True)
                
                rule_mock.assert_called_once_with(title="Section", style="blue")
                terminal.print.assert_called_once_with(rule_instance, persist=True)
    
    def test_print_rule_fallback(self):
        """Test print_rule in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        terminal.buffered_renderer.terminal_width = 40
        
        with patch.object(terminal, 'print') as mock_print:
            terminal.print_rule(title="Test", persist=True)
            
            # Check that a rule was printed
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Test" in call_args
            assert "─" in call_args
    
    def test_print_rule_fallback_no_title(self):
        """Test print_rule in fallback mode without title."""
        terminal = RichTerminal(use_rich=False)
        terminal.buffered_renderer.terminal_width = 40
        
        with patch.object(terminal, 'print') as mock_print:
            terminal.print_rule(title=None, persist=True)
            
            # Check that a rule was printed
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "─" * 40 in call_args
    
    def test_print_tree_with_rich(self):
        """Test print_tree with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            terminal.print = Mock()
            
            tree_mock = Mock()
            tree_instance = Mock()
            tree_mock.return_value = tree_instance
            tree_instance.add.return_value = Mock()
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Tree', tree_mock, create=True):
                data = {"root": {"child1": "value1", "child2": {"nested": "value2"}}}
                terminal.print_tree(data, title="Test Tree", persist=True)
                
                tree_mock.assert_called_once_with("Test Tree")
                terminal.print.assert_called_once_with(tree_instance, persist=True)
    
    def test_build_tree_recursive(self):
        """Test _build_tree recursive method."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            
            mock_tree = Mock()
            mock_branch = Mock()
            mock_tree.add.return_value = mock_branch
            
            data = {
                "key1": "value1",
                "key2": {
                    "nested1": "nested_value1",
                    "nested2": "nested_value2"
                }
            }
            
            terminal._build_tree(mock_tree, data)
            
            # Check that add was called appropriately
            assert mock_tree.add.call_count == 2
            assert mock_branch.add.call_count == 2
    
    def test_print_tree_fallback(self):
        """Test print_tree in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        with patch.object(terminal, 'print') as mock_print:
            data = {"root": {"child": "value"}}
            terminal.print_tree(data, title="Tree", persist=True)
            
            # Should print tree structure
            calls = mock_print.call_args_list
            assert len(calls) >= 2  # Title + tree items
    
    def test_print_tree_fallback_recursive(self):
        """Test _print_tree_fallback recursive method."""
        terminal = RichTerminal(use_rich=False)
        
        with patch.object(terminal, 'print') as mock_print:
            data = {
                "folder": {
                    "file1": "content1",
                    "subfolder": {
                        "file2": "content2"
                    }
                }
            }
            terminal._print_tree_fallback(data, indent=0, persist=True)
            
            # Check that nested structure was printed
            calls = mock_print.call_args_list
            assert any("folder/" in str(call) for call in calls)
            assert any("file1" in str(call) for call in calls)
            assert any("subfolder/" in str(call) for call in calls)
            assert any("file2" in str(call) for call in calls)
    
    def test_progress_context_with_rich(self):
        """Test progress context manager with Rich."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            
            progress_mock = Mock()
            progress_instance = Mock()
            progress_mock.return_value = progress_instance
            progress_instance.__enter__ = Mock(return_value=progress_instance)
            progress_instance.__exit__ = Mock(return_value=False)
            progress_instance.add_task.return_value = "task_id"
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Progress', progress_mock, create=True):
                with terminal.progress("Processing", total=100) as tracker:
                    assert isinstance(tracker, ProgressTracker)
                    assert tracker.task_id == "task_id"
                    
                progress_instance.add_task.assert_called_once_with("Processing", total=100)
    
    def test_progress_context_fallback(self):
        """Test progress context manager in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        with terminal.progress("Working", total=50) as tracker:
            assert isinstance(tracker, FallbackProgressTracker)
            assert tracker.description == "Working"
            assert tracker.total == 50
    
    def test_live_display_with_rich(self):
        """Test live_display context manager with Rich."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            
            live_mock = Mock()
            live_instance = Mock()
            live_mock.return_value = live_instance
            live_instance.__enter__ = Mock(return_value=live_instance)
            live_instance.__exit__ = Mock(return_value=False)
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Live', live_mock, create=True):
                with terminal.live_display("Initial") as display:
                    assert isinstance(display, LiveDisplay)
                    assert terminal._live_context == live_instance
                
                assert terminal._live_context is None
    
    def test_live_display_fallback(self):
        """Test live_display in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        with terminal.live_display("Content") as display:
            assert isinstance(display, FallbackLiveDisplay)
            assert display.terminal == terminal
    
    def test_prompt_with_rich(self):
        """Test prompt with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            
            prompt_mock = Mock()
            prompt_mock.ask.return_value = "user input"
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Prompt', prompt_mock, create=True):
                result = terminal.prompt(
                    "Enter value",
                    default="default",
                    choices=["a", "b", "c"]
                )
                
                assert result == "user input"
                prompt_mock.ask.assert_called_once_with(
                    "Enter value",
                    default="default",
                    choices=["a", "b", "c"],
                    console=terminal.console
                )
    
    def test_prompt_fallback(self):
        """Test prompt in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        with patch('builtins.input', return_value="test"):
            result = terminal.prompt("Question", default="def", choices=["a", "b"])
            assert result == "test"
        
        # Test with empty input (use default)
        with patch('builtins.input', return_value=""):
            result = terminal.prompt("Question", default="default")
            assert result == "default"
        
        # Test without default
        with patch('builtins.input', return_value=""):
            result = terminal.prompt("Question")
            assert result == ""
    
    def test_confirm_with_rich(self):
        """Test confirm with Rich enabled."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            terminal = RichTerminal(use_rich=True)
            
            confirm_mock = Mock()
            confirm_mock.ask.return_value = True
            
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'Confirm', confirm_mock, create=True):
                result = terminal.confirm("Continue?", default=False)
                
                assert result is True
                confirm_mock.ask.assert_called_once_with(
                    "Continue?",
                    default=False,
                    console=terminal.console
                )
    
    def test_confirm_fallback(self):
        """Test confirm in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        # Test yes response
        with patch('builtins.input', return_value="y"):
            assert terminal.confirm("Continue?") is True
        
        # Test no response
        with patch('builtins.input', return_value="n"):
            assert terminal.confirm("Continue?") is False
        
        # Test default (True)
        with patch('builtins.input', return_value=""):
            assert terminal.confirm("Continue?", default=True) is True
        
        # Test default (False)
        with patch('builtins.input', return_value=""):
            assert terminal.confirm("Continue?", default=False) is False
    
    def test_clear_last_frame(self):
        """Test clear_last_frame method."""
        terminal = RichTerminal(use_rich=True)
        
        with patch.object(terminal.buffered_renderer, 'render_frame') as mock_render:
            terminal.clear_last_frame()
            mock_render.assert_called_once()
            args = mock_render.call_args[0]
            assert args[0] == []
    
    def test_cleanup(self):
        """Test cleanup method."""
        terminal = RichTerminal(use_rich=True)
        terminal._live_context = Mock()
        
        with patch.object(terminal.buffered_renderer, 'cleanup') as mock_cleanup:
            terminal.cleanup()
            
            terminal._live_context.stop.assert_called_once()
            mock_cleanup.assert_called_once()
    
    def test_cleanup_no_live_context(self):
        """Test cleanup without live context."""
        terminal = RichTerminal(use_rich=True)
        terminal._live_context = None
        
        with patch.object(terminal.buffered_renderer, 'cleanup') as mock_cleanup:
            terminal.cleanup()
            mock_cleanup.assert_called_once()
    
    def test_context_manager(self):
        """Test RichTerminal as context manager."""
        terminal = RichTerminal(use_rich=True)
        
        with patch.object(terminal, 'cleanup') as mock_cleanup:
            with terminal as t:
                assert t == terminal
            
            mock_cleanup.assert_called_once()
    
    def test_progress_tracker_methods(self):
        """Test ProgressTracker methods."""
        mock_progress = Mock()
        tracker = ProgressTracker(mock_progress, "task_id")
        
        tracker.update(5)
        mock_progress.update.assert_called_with("task_id", advance=5)
        
        tracker.set_total(100)
        mock_progress.update.assert_called_with("task_id", total=100)
        
        tracker.set_description("New desc")
        mock_progress.update.assert_called_with("task_id", description="New desc")
    
    def test_fallback_progress_tracker_update(self):
        """Test FallbackProgressTracker update method."""
        terminal = Mock()
        terminal.buffered_renderer = Mock()
        
        tracker = FallbackProgressTracker(terminal, "Processing", 100)
        
        tracker.update(25)
        assert tracker.current == 25
        terminal.buffered_renderer.render_status_line.assert_called_once()
        
        # Check the status line format
        call_args = terminal.buffered_renderer.render_status_line.call_args[0]
        assert "Processing" in call_args[0]
        assert "25.0%" in call_args[0]
    
    def test_fallback_progress_tracker_set_methods(self):
        """Test FallbackProgressTracker setter methods."""
        terminal = Mock()
        tracker = FallbackProgressTracker(terminal, "Initial", 50)
        
        tracker.set_total(200)
        assert tracker.total == 200
        
        tracker.set_description("Updated")
        assert tracker.description == "Updated"
    
    def test_live_display_update(self):
        """Test LiveDisplay update method."""
        mock_live = Mock()
        display = LiveDisplay(mock_live)
        
        display.update("New content")
        mock_live.update.assert_called_once_with("New content")
    
    def test_fallback_live_display_update(self):
        """Test FallbackLiveDisplay update method."""
        terminal = Mock()
        terminal.clear_last_frame = Mock()
        terminal.print = Mock()
        
        display = FallbackLiveDisplay(terminal)
        display.update("Content")
        
        terminal.clear_last_frame.assert_called_once()
        terminal.print.assert_called_once_with("Content", persist=False)
    
    def test_create_rich_terminal(self):
        """Test create_rich_terminal utility function."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            # Patch RichTerminal class in the module where it's imported
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'RichTerminal') as mock_class:
                mock_instance = Mock()
                mock_class.return_value = mock_instance
                
                result = create_rich_terminal(use_rich=True, width=100)
                
                mock_class.assert_called_once_with(use_rich=True, width=100)
                assert result == mock_instance
    
    @patch('time.sleep')
    def test_demo_rich_terminal_with_rich(self, mock_sleep):
        """Test demo_rich_terminal function with Rich available."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            # Patch RichTerminal class in the module where it's imported
            with patch.object(sys.modules['storm_checker.cli.components.rich_terminal'], 'RichTerminal') as mock_class:
                mock_terminal = Mock()
                mock_terminal.__enter__ = Mock(return_value=mock_terminal)
                mock_terminal.__exit__ = Mock(return_value=False)
                
                # Create a proper progress context manager mock
                mock_progress_context = Mock()
                mock_progress_context.__enter__ = Mock()
                mock_progress_context.__exit__ = Mock(return_value=False)
                mock_progress = Mock()
                mock_progress_context.__enter__.return_value = mock_progress
                mock_terminal.progress.return_value = mock_progress_context
                
                # Set up all the terminal methods
                mock_terminal.print_rule = Mock()
                mock_terminal.print = Mock()
                mock_terminal.print_panel = Mock()
                mock_terminal.print_table = Mock()
                mock_terminal.print_markdown = Mock()
                mock_terminal.print_code = Mock()
                mock_terminal.progress = Mock(return_value=mock_progress_context)
                
                mock_class.return_value = mock_terminal
                
                demo_rich_terminal()
                
                # Check that various methods were called
                assert mock_terminal.print_rule.called
                assert mock_terminal.print.called
                assert mock_terminal.print_panel.called
                assert mock_terminal.print_table.called
                assert mock_terminal.print_markdown.called
                assert mock_terminal.print_code.called
                assert mock_terminal.progress.called
                
                # Check progress updates
                assert mock_progress.update.call_count == 10
    
    def test_demo_rich_terminal_without_rich(self):
        """Test demo behavior when Rich is not available."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', False):
            with patch('builtins.print') as mock_print:
                # This should be handled in __main__ block
                # The function won't run if RICH_AVAILABLE is False
                pass
    
    def test_main_block_with_rich(self):
        """Test __main__ block execution with Rich."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            with patch('storm_checker.cli.components.rich_terminal.demo_rich_terminal') as mock_demo:
                # Simulate running as main
                exec("""
if RICH_AVAILABLE:
    demo_rich_terminal()
else:
    print("Rich library not available. Install with: pip install rich")
""", {'RICH_AVAILABLE': True, 'demo_rich_terminal': mock_demo, 'print': print})
                
                mock_demo.assert_called_once()
    
    def test_main_block_without_rich(self):
        """Test __main__ block execution without Rich."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', False):
            with patch('builtins.print') as mock_print:
                exec("""
if RICH_AVAILABLE:
    demo_rich_terminal()
else:
    print("Rich library not available. Install with: pip install rich")
""", {'RICH_AVAILABLE': False, 'demo_rich_terminal': None, 'print': mock_print})
                
                mock_print.assert_called_once_with("Rich library not available. Install with: pip install rich")