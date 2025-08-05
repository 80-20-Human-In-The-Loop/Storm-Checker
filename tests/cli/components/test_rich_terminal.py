"""
Comprehensive Tests for Rich Terminal
====================================
Tests for Rich library integration with BufferedRenderer and fallback support.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from contextlib import contextmanager
from typing import Any, Optional, List, Dict
import tempfile
import shutil
from pathlib import Path

from storm_checker.cli.components.rich_terminal import (
    RichTerminal, ProgressTracker, FallbackProgressTracker,
    LiveDisplay, FallbackLiveDisplay, create_rich_terminal, demo_rich_terminal
)


class TestRichTerminal:
    """Test the RichTerminal class."""
    
    @pytest.fixture
    def mock_buffered_renderer(self):
        """Create mock BufferedRenderer."""
        with patch('storm_checker.cli.components.rich_terminal.BufferedRenderer') as mock_br:
            mock_instance = Mock()
            mock_instance.terminal_width = 80
            mock_br.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_rich_imports(self):
        """Mock Rich library imports."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
            with patch('storm_checker.cli.components.rich_terminal.Console') as mock_console:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance
                yield mock_console_instance
    
    @pytest.fixture
    def mock_rich_unavailable(self):
        """Mock Rich library as unavailable."""
        with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', False):
            with patch('storm_checker.cli.components.rich_terminal.Console', None):
                yield
    
    def test_initialization_with_rich_available(self, mock_buffered_renderer, mock_rich_imports):
        """Test RichTerminal initialization when Rich is available."""
        terminal = RichTerminal(
            use_rich=True,
            width=100,
            height=50,
            theme="custom"
        )
        
        assert terminal.use_rich is True
        assert terminal.console is not None
        assert terminal._live_context is None
        assert terminal.buffered_renderer == mock_buffered_renderer
    
    def test_initialization_with_rich_unavailable(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test RichTerminal initialization when Rich is unavailable."""
        terminal = RichTerminal(use_rich=True)
        
        assert terminal.use_rich is False
        assert terminal.console is None
        assert terminal.buffered_renderer == mock_buffered_renderer
    
    def test_initialization_rich_disabled(self, mock_buffered_renderer, mock_rich_imports):
        """Test RichTerminal initialization with Rich disabled."""
        terminal = RichTerminal(use_rich=False)
        
        assert terminal.use_rich is False
        assert terminal.console is None
    
    def test_initialization_defaults(self, mock_buffered_renderer, mock_rich_imports):
        """Test RichTerminal initialization with default parameters."""
        terminal = RichTerminal()
        
        assert terminal.use_rich is True
        assert terminal.console is not None
        assert terminal._live_context is None
    
    def test_print_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test print method with Rich available."""
        terminal = RichTerminal()
        
        # Mock console.capture context manager
        mock_capture = Mock()
        mock_capture.get.return_value = "test output\nline 2"
        mock_capture_context = Mock()
        mock_capture_context.__enter__ = Mock(return_value=mock_capture)
        mock_capture_context.__exit__ = Mock(return_value=False)
        terminal.console.capture.return_value = mock_capture_context
        
        terminal.print("test", "message", style="bold", highlight=False, persist=True)
        
        terminal.console.print.assert_called_once_with(
            "test", "message",
            style="bold",
            highlight=False,
            markup=True,
            emoji=True
        )
        mock_buffered_renderer.render_frame.assert_called_once()
    
    def test_print_with_rich_no_persist(self, mock_buffered_renderer, mock_rich_imports):
        """Test print method with Rich available but no persist."""
        terminal = RichTerminal()
        
        # Mock console.capture
        mock_capture = Mock()
        mock_capture.get.return_value = "test output"
        mock_capture_context = Mock()
        mock_capture_context.__enter__ = Mock(return_value=mock_capture)
        mock_capture_context.__exit__ = Mock(return_value=False)
        terminal.console.capture.return_value = mock_capture_context
        
        with patch('builtins.print') as mock_print:
            terminal.print("test", persist=False)
            
            mock_print.assert_called_once_with("test output", end='')
            mock_buffered_renderer.render_frame.assert_not_called()
    
    def test_print_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print method without Rich available."""
        terminal = RichTerminal()
        
        terminal.print("test", "message", persist=True)
        
        mock_buffered_renderer.render_persistent_message.assert_called_once_with("test message")
    
    def test_print_without_rich_no_persist(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print method without Rich and no persist."""
        terminal = RichTerminal()
        
        with patch('builtins.print') as mock_print:
            terminal.print("test", "message", persist=False)
            
            mock_print.assert_called_once_with("test message")
            mock_buffered_renderer.render_persistent_message.assert_not_called()
    
    def test_print_panel_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test print_panel method with Rich available."""
        terminal = RichTerminal()
        
        # Mock Panel and console.capture
        with patch('storm_checker.cli.components.rich_terminal.Panel') as mock_panel:
            mock_panel_instance = Mock()
            mock_panel.return_value = mock_panel_instance
            
            mock_capture = Mock()
            mock_capture.get.return_value = "panel output"
            mock_capture_context = Mock()
            mock_capture_context.__enter__ = Mock(return_value=mock_capture)
            mock_capture_context.__exit__ = Mock(return_value=False)
            terminal.console.capture.return_value = mock_capture_context
            
            terminal.print_panel(
                "content",
                title="Test Title",
                subtitle="Test Subtitle",
                style="custom",
                border_style="red",
                expand=False
            )
            
            mock_panel.assert_called_once_with(
                "content",
                title="Test Title",
                subtitle="Test Subtitle",
                style="custom",
                border_style="red",
                expand=False
            )
    
    def test_print_panel_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print_panel method without Rich available."""
        terminal = RichTerminal()
        
        terminal.print_panel(
            "content",
            title="Test Title",
            subtitle="Test Subtitle"
        )
        
        # Should call render_persistent_message multiple times for fallback
        assert mock_buffered_renderer.render_persistent_message.call_count >= 3
    
    def test_print_table_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test print_table method with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Table') as mock_table:
            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            
            # Mock console.capture
            mock_capture = Mock()
            mock_capture.get.return_value = "table output"
            mock_capture_context = Mock()
            mock_capture_context.__enter__ = Mock(return_value=mock_capture)
            mock_capture_context.__exit__ = Mock(return_value=False)
            terminal.console.capture.return_value = mock_capture_context
            
            data = [["A", "B"], ["C", "D"]]
            headers = ["Col1", "Col2"]
            
            terminal.print_table(data, headers=headers, title="Test Table")
            
            mock_table.assert_called_once_with(title="Test Table", style="default")
            mock_table_instance.add_column.assert_has_calls([
                call("Col1", style="bold"),
                call("Col2", style="bold")
            ])
            mock_table_instance.add_row.assert_has_calls([
                call("A", "B"),
                call("C", "D")
            ])
    
    def test_print_table_without_headers_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test print_table method without headers with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Table') as mock_table:
            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            
            # Mock console.capture
            mock_capture = Mock()
            mock_capture.get.return_value = "table output"
            mock_capture_context = Mock()
            mock_capture_context.__enter__ = Mock(return_value=mock_capture)
            mock_capture_context.__exit__ = Mock(return_value=False)
            terminal.console.capture.return_value = mock_capture_context
            
            data = [["A", "B"], ["C", "D"]]
            
            terminal.print_table(data)
            
            # Should auto-generate column headers
            mock_table_instance.add_column.assert_has_calls([
                call("Col 1"),
                call("Col 2")
            ])
    
    def test_print_table_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print_table method without Rich available."""
        terminal = RichTerminal()
        
        data = [["A", "B"], ["C", "D"]]
        headers = ["Col1", "Col2"]
        
        terminal.print_table(data, headers=headers, title="Test Table")
        
        # Should call render_persistent_message for fallback table
        assert mock_buffered_renderer.render_persistent_message.call_count >= 4
    
    def test_print_markdown_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test print_markdown method with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Markdown') as mock_markdown:
            mock_md_instance = Mock()
            mock_markdown.return_value = mock_md_instance
            
            # Mock console.capture
            mock_capture = Mock()
            mock_capture.get.return_value = "markdown output"
            mock_capture_context = Mock()
            mock_capture_context.__enter__ = Mock(return_value=mock_capture)
            mock_capture_context.__exit__ = Mock(return_value=False)
            terminal.console.capture.return_value = mock_capture_context
            
            terminal.print_markdown("# Header\nContent", style="custom")
            
            mock_markdown.assert_called_once_with("# Header\nContent", style="custom")
    
    def test_print_markdown_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print_markdown method without Rich available."""
        terminal = RichTerminal()
        
        markdown_content = "# Header\n## Subheader\n- Item\nRegular text"
        
        terminal.print_markdown(markdown_content)
        
        # Should call render_persistent_message for each line
        assert mock_buffered_renderer.render_persistent_message.call_count == 4
    
    def test_print_code_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test print_code method with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Syntax') as mock_syntax:
            mock_syntax_instance = Mock()
            mock_syntax.return_value = mock_syntax_instance
            
            # Mock console.capture
            mock_capture = Mock()
            mock_capture.get.return_value = "code output"
            mock_capture_context = Mock()
            mock_capture_context.__enter__ = Mock(return_value=mock_capture)
            mock_capture_context.__exit__ = Mock(return_value=False)
            terminal.console.capture.return_value = mock_capture_context
            
            terminal.print_code("print('hello')", language="python", theme="dark", line_numbers=True)
            
            mock_syntax.assert_called_once_with(
                "print('hello')",
                "python",
                theme="dark",
                line_numbers=True
            )
    
    def test_print_code_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print_code method without Rich available."""
        terminal = RichTerminal()
        
        code = "print('hello')\nprint('world')"
        
        terminal.print_code(code, language="python")
        
        # Should call render_persistent_message for fallback code display
        assert mock_buffered_renderer.render_persistent_message.call_count >= 4
    
    def test_print_rule_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test print_rule method with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Rule') as mock_rule:
            mock_rule_instance = Mock()
            mock_rule.return_value = mock_rule_instance
            
            # Mock console.capture
            mock_capture = Mock()
            mock_capture.get.return_value = "rule output"
            mock_capture_context = Mock()
            mock_capture_context.__enter__ = Mock(return_value=mock_capture)
            mock_capture_context.__exit__ = Mock(return_value=False)
            terminal.console.capture.return_value = mock_capture_context
            
            terminal.print_rule(title="Test Rule", style="bold")
            
            mock_rule.assert_called_once_with(title="Test Rule", style="bold")
    
    def test_print_rule_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print_rule method without Rich available."""
        terminal = RichTerminal()
        mock_buffered_renderer.terminal_width = 20
        
        terminal.print_rule(title="Test")
        
        mock_buffered_renderer.render_persistent_message.assert_called_once()
        # Check that the call contains a centered rule
        call_args = mock_buffered_renderer.render_persistent_message.call_args[0][0]
        assert "Test" in call_args
        assert "─" in call_args
    
    def test_print_rule_without_title_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print_rule method without title and without Rich."""
        terminal = RichTerminal()
        mock_buffered_renderer.terminal_width = 10
        
        terminal.print_rule()
        
        mock_buffered_renderer.render_persistent_message.assert_called_once()
        # Check that the call contains just dashes
        call_args = mock_buffered_renderer.render_persistent_message.call_args[0][0]
        assert call_args.count("─") == 10
    
    def test_print_tree_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test print_tree method with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Tree') as mock_tree:
            mock_tree_instance = Mock()
            mock_tree.return_value = mock_tree_instance
            
            # Mock console.capture
            mock_capture = Mock()
            mock_capture.get.return_value = "tree output"
            mock_capture_context = Mock()
            mock_capture_context.__enter__ = Mock(return_value=mock_capture)
            mock_capture_context.__exit__ = Mock(return_value=False)
            terminal.console.capture.return_value = mock_capture_context
            
            data = {"root": {"child1": "value1", "child2": {"grandchild": "value2"}}}
            
            terminal.print_tree(data, title="Test Tree")
            
            mock_tree.assert_called_once_with("Test Tree")
    
    def test_print_tree_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test print_tree method without Rich available."""
        terminal = RichTerminal()
        
        data = {"root": {"child1": "value1", "child2": "value2"}}
        
        terminal.print_tree(data, title="Test Tree")
        
        # Should call render_persistent_message for fallback tree
        assert mock_buffered_renderer.render_persistent_message.call_count >= 3
    
    def test_build_tree_recursive(self, mock_buffered_renderer, mock_rich_imports):
        """Test _build_tree method with nested dictionaries."""
        terminal = RichTerminal()
        
        mock_tree = Mock()
        mock_branch = Mock()
        mock_tree.add.return_value = mock_branch
        
        data = {
            "simple": "value",
            "nested": {
                "child": "child_value"
            }
        }
        
        terminal._build_tree(mock_tree, data)
        
        # Should add simple value and nested branch
        mock_tree.add.assert_any_call("simple: value")
        mock_tree.add.assert_any_call("nested")
        mock_branch.add.assert_called_once_with("child: child_value")
    
    def test_print_tree_fallback_recursive(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test _print_tree_fallback method with nested data."""
        terminal = RichTerminal()
        
        data = {
            "file.txt": "content",
            "folder": {
                "subfolder": {
                    "nested.txt": "nested_content"
                },
                "another.txt": "more_content"
            }
        }
        
        terminal._print_tree_fallback(data, indent=0)
        
        # Should call render_persistent_message for each item
        assert mock_buffered_renderer.render_persistent_message.call_count >= 4
    
    def test_progress_context_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test progress context manager with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Progress') as mock_progress_class:
            with patch('rich.progress.SpinnerColumn') as mock_spinner:
                with patch('rich.progress.TextColumn') as mock_text:
                    with patch('rich.progress.BarColumn') as mock_bar:
                        mock_progress_instance = Mock()
                        mock_progress_class.return_value.__enter__ = Mock(return_value=mock_progress_instance)
                        mock_progress_class.return_value.__exit__ = Mock(return_value=False)
                        mock_progress_instance.add_task.return_value = "task_id"
                        
                        with terminal.progress("Testing...", total=100) as tracker:
                            assert isinstance(tracker, ProgressTracker)
                            assert tracker.progress == mock_progress_instance
                            assert tracker.task_id == "task_id"
    
    def test_progress_context_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test progress context manager without Rich available."""
        terminal = RichTerminal()
        
        with terminal.progress("Testing...", total=50) as tracker:
            assert isinstance(tracker, FallbackProgressTracker)
            assert tracker.terminal == terminal
            assert tracker.description == "Testing..."
            assert tracker.total == 50
    
    def test_live_display_context_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test live_display context manager with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Live') as mock_live_class:
            mock_live_instance = Mock()
            mock_live_class.return_value.__enter__ = Mock(return_value=mock_live_instance)
            mock_live_class.return_value.__exit__ = Mock(return_value=False)
            
            with terminal.live_display("Initial content") as display:
                assert isinstance(display, LiveDisplay)
                assert display.live == mock_live_instance
                assert terminal._live_context == mock_live_instance
            
            assert terminal._live_context is None
    
    def test_live_display_context_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test live_display context manager without Rich available."""
        terminal = RichTerminal()
        
        with terminal.live_display("Initial content") as display:
            assert isinstance(display, FallbackLiveDisplay)
            assert display.terminal == terminal
    
    def test_prompt_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test prompt method with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Prompt') as mock_prompt:
            mock_prompt.ask.return_value = "user_response"
            
            result = terminal.prompt("Question?", default="default", choices=["a", "b"])
            
            assert result == "user_response"
            mock_prompt.ask.assert_called_once_with(
                "Question?",
                default="default",
                choices=["a", "b"],
                console=terminal.console
            )
    
    def test_prompt_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test prompt method without Rich available."""
        terminal = RichTerminal()
        
        with patch('builtins.input', return_value="user_input"):
            result = terminal.prompt("Question?", default="default", choices=["a", "b"])
            
            assert result == "user_input"
    
    def test_prompt_without_rich_empty_response(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test prompt method without Rich with empty response."""
        terminal = RichTerminal()
        
        with patch('builtins.input', return_value=""):
            result = terminal.prompt("Question?", default="default")
            
            assert result == "default"
    
    def test_prompt_without_rich_no_default(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test prompt method without Rich with no default."""
        terminal = RichTerminal()
        
        with patch('builtins.input', return_value=""):
            result = terminal.prompt("Question?")
            
            assert result == ""
    
    def test_confirm_with_rich(self, mock_buffered_renderer, mock_rich_imports):
        """Test confirm method with Rich available."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.Confirm') as mock_confirm:
            mock_confirm.ask.return_value = True
            
            result = terminal.confirm("Proceed?", default=False)
            
            assert result is True
            mock_confirm.ask.assert_called_once_with(
                "Proceed?",
                default=False,
                console=terminal.console
            )
    
    def test_confirm_without_rich(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test confirm method without Rich available."""
        terminal = RichTerminal()
        
        with patch('builtins.input', return_value="y"):
            result = terminal.confirm("Proceed?", default=False)
            
            assert result is True
    
    def test_confirm_without_rich_no_response(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test confirm method without Rich with empty response."""
        terminal = RichTerminal()
        
        with patch('builtins.input', return_value=""):
            result = terminal.confirm("Proceed?", default=True)
            
            assert result is True
    
    def test_confirm_without_rich_negative(self, mock_buffered_renderer, mock_rich_unavailable):
        """Test confirm method without Rich with negative response."""
        terminal = RichTerminal()
        
        with patch('builtins.input', return_value="n"):
            result = terminal.confirm("Proceed?", default=True)
            
            assert result is False
    
    def test_clear_last_frame(self, mock_buffered_renderer, mock_rich_imports):
        """Test clear_last_frame method."""
        terminal = RichTerminal()
        
        with patch('storm_checker.cli.components.rich_terminal.RenderMode') as mock_render_mode:
            mock_render_mode.REPLACE_LAST = "REPLACE_LAST"
            terminal.clear_last_frame()
            
            mock_buffered_renderer.render_frame.assert_called_once_with([], "REPLACE_LAST")
    
    def test_cleanup_with_live_context(self, mock_buffered_renderer, mock_rich_imports):
        """Test cleanup method with active live context."""
        terminal = RichTerminal()
        
        mock_live = Mock()
        terminal._live_context = mock_live
        
        terminal.cleanup()
        
        mock_live.stop.assert_called_once()
        mock_buffered_renderer.cleanup.assert_called_once()
    
    def test_cleanup_without_live_context(self, mock_buffered_renderer, mock_rich_imports):
        """Test cleanup method without live context."""
        terminal = RichTerminal()
        
        terminal.cleanup()
        
        mock_buffered_renderer.cleanup.assert_called_once()
    
    def test_context_manager(self, mock_buffered_renderer, mock_rich_imports):
        """Test RichTerminal as context manager."""
        with patch.object(RichTerminal, 'cleanup') as mock_cleanup:
            with RichTerminal() as terminal:
                assert isinstance(terminal, RichTerminal)
            
            mock_cleanup.assert_called_once()


class TestProgressTracker:
    """Test the ProgressTracker class."""
    
    @pytest.fixture
    def mock_progress_and_task(self):
        """Create mock Progress and TaskID."""
        mock_progress = Mock()
        mock_task_id = "test_task_id"
        return mock_progress, mock_task_id
    
    def test_initialization(self, mock_progress_and_task):
        """Test ProgressTracker initialization."""
        mock_progress, mock_task_id = mock_progress_and_task
        tracker = ProgressTracker(mock_progress, mock_task_id)
        
        assert tracker.progress == mock_progress
        assert tracker.task_id == mock_task_id
    
    def test_update(self, mock_progress_and_task):
        """Test update method."""
        mock_progress, mock_task_id = mock_progress_and_task
        tracker = ProgressTracker(mock_progress, mock_task_id)
        
        tracker.update(5)
        
        mock_progress.update.assert_called_once_with(mock_task_id, advance=5)
    
    def test_update_default(self, mock_progress_and_task):
        """Test update method with default advance."""
        mock_progress, mock_task_id = mock_progress_and_task
        tracker = ProgressTracker(mock_progress, mock_task_id)
        
        tracker.update()
        
        mock_progress.update.assert_called_once_with(mock_task_id, advance=1)
    
    def test_set_total(self, mock_progress_and_task):
        """Test set_total method."""
        mock_progress, mock_task_id = mock_progress_and_task
        tracker = ProgressTracker(mock_progress, mock_task_id)
        
        tracker.set_total(100)
        
        mock_progress.update.assert_called_once_with(mock_task_id, total=100)
    
    def test_set_description(self, mock_progress_and_task):
        """Test set_description method."""
        mock_progress, mock_task_id = mock_progress_and_task
        tracker = ProgressTracker(mock_progress, mock_task_id)
        
        tracker.set_description("New description")
        
        mock_progress.update.assert_called_once_with(mock_task_id, description="New description")


class TestFallbackProgressTracker:
    """Test the FallbackProgressTracker class."""
    
    @pytest.fixture
    def mock_terminal(self):
        """Create mock RichTerminal."""
        mock_terminal = Mock(spec=RichTerminal)
        mock_terminal.buffered_renderer = Mock()
        return mock_terminal
    
    def test_initialization(self, mock_terminal):
        """Test FallbackProgressTracker initialization."""
        tracker = FallbackProgressTracker(mock_terminal, "Testing", 50)
        
        assert tracker.terminal == mock_terminal
        assert tracker.description == "Testing"
        assert tracker.total == 50
        assert tracker.current == 0
    
    def test_initialization_default_total(self, mock_terminal):
        """Test FallbackProgressTracker initialization with default total."""
        tracker = FallbackProgressTracker(mock_terminal, "Testing", None)
        
        assert tracker.total == 100
    
    def test_update(self, mock_terminal):
        """Test update method."""
        tracker = FallbackProgressTracker(mock_terminal, "Testing", 10)
        
        tracker.update(3)
        
        assert tracker.current == 3
        mock_terminal.buffered_renderer.render_status_line.assert_called_once()
        
        # Check the status line contains progress bar
        call_args = mock_terminal.buffered_renderer.render_status_line.call_args[0][0]
        assert "Testing" in call_args
        assert "30.0%" in call_args
        assert "█" in call_args or "░" in call_args
    
    def test_update_default_advance(self, mock_terminal):
        """Test update method with default advance."""
        tracker = FallbackProgressTracker(mock_terminal, "Testing", 10)
        
        tracker.update()
        
        assert tracker.current == 1
    
    def test_set_total(self, mock_terminal):
        """Test set_total method."""
        tracker = FallbackProgressTracker(mock_terminal, "Testing", 10)
        
        tracker.set_total(50)
        
        assert tracker.total == 50
    
    def test_set_description(self, mock_terminal):
        """Test set_description method."""
        tracker = FallbackProgressTracker(mock_terminal, "Testing", 10)
        
        tracker.set_description("New description")
        
        assert tracker.description == "New description"


class TestLiveDisplay:
    """Test the LiveDisplay class."""
    
    def test_initialization(self):
        """Test LiveDisplay initialization."""
        mock_live = Mock()
        display = LiveDisplay(mock_live)
        
        assert display.live == mock_live
    
    def test_update(self):
        """Test update method."""
        mock_live = Mock()
        display = LiveDisplay(mock_live)
        
        display.update("New content")
        
        mock_live.update.assert_called_once_with("New content")


class TestFallbackLiveDisplay:
    """Test the FallbackLiveDisplay class."""
    
    @pytest.fixture
    def mock_terminal(self):
        """Create mock RichTerminal."""
        return Mock(spec=RichTerminal)
    
    def test_initialization(self, mock_terminal):
        """Test FallbackLiveDisplay initialization."""
        display = FallbackLiveDisplay(mock_terminal)
        
        assert display.terminal == mock_terminal
    
    def test_update(self, mock_terminal):
        """Test update method."""
        display = FallbackLiveDisplay(mock_terminal)
        
        display.update("New content")
        
        mock_terminal.clear_last_frame.assert_called_once()
        mock_terminal.print.assert_called_once_with("New content", persist=False)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_rich_terminal(self):
        """Test create_rich_terminal function."""
        with patch('storm_checker.cli.components.rich_terminal.BufferedRenderer'):
            with patch('storm_checker.cli.components.rich_terminal.RICH_AVAILABLE', True):
                with patch('storm_checker.cli.components.rich_terminal.Console'):
                    terminal = create_rich_terminal(width=100, height=50)
                    
                    assert isinstance(terminal, RichTerminal)
    
    def test_demo_rich_terminal(self):
        """Test demo_rich_terminal function."""
        with patch('storm_checker.cli.components.rich_terminal.RichTerminal') as mock_terminal_class:
            mock_terminal_instance = Mock()
            # Set up context manager properly
            mock_context_manager = Mock()
            mock_context_manager.__enter__ = Mock(return_value=mock_terminal_instance)
            mock_context_manager.__exit__ = Mock(return_value=False)
            mock_terminal_class.return_value = mock_context_manager
            
            # Mock the progress context manager
            mock_progress_context = Mock()
            mock_progress_context.__enter__ = Mock(return_value=Mock())
            mock_progress_context.__exit__ = Mock(return_value=False)
            mock_terminal_instance.progress.return_value = mock_progress_context
            
            with patch('time.sleep'):  # Speed up the demo
                demo_rich_terminal()
                
                # Should call various terminal methods
                mock_terminal_instance.print_rule.assert_called()
                mock_terminal_instance.print.assert_called()
                mock_terminal_instance.print_panel.assert_called()
                mock_terminal_instance.print_table.assert_called()
                mock_terminal_instance.print_markdown.assert_called()
                mock_terminal_instance.print_code.assert_called()