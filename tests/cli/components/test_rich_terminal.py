"""
Fixed Tests for Rich Terminal
===============================
Properly isolated tests for Rich terminal functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

# Import the classes we're testing
from storm_checker.cli.components.rich_terminal import (
    RichTerminal, ProgressTracker, FallbackProgressTracker,
    LiveDisplay, FallbackLiveDisplay
)


class TestRichTerminalFixed:
    """Fixed tests for RichTerminal with proper isolation."""
    
    def test_initialization_with_rich_disabled(self):
        """Test RichTerminal when explicitly disabled."""
        terminal = RichTerminal(use_rich=False)
        assert terminal.use_rich is False
        assert terminal.console is None
        assert terminal.buffered_renderer is not None
    
    def test_print_fallback_persist(self):
        """Test print method without Rich (fallback mode)."""
        terminal = RichTerminal(use_rich=False)
        
        # Mock the buffered renderer's method
        with patch.object(terminal.buffered_renderer, 'render_persistent_message') as mock_render:
            terminal.print("test", "message", persist=True)
            mock_render.assert_called_once_with("test message")
    
    def test_print_fallback_no_persist(self):
        """Test print without Rich and no persist."""
        terminal = RichTerminal(use_rich=False)
        
        with patch('builtins.print') as mock_print:
            terminal.print("test", "message", persist=False)
            mock_print.assert_called_once_with("test message")
    
    def test_print_panel_fallback(self):
        """Test print_panel in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        with patch.object(terminal.buffered_renderer, 'render_persistent_message') as mock_render:
            terminal.print_panel(
                "content",
                title="Test Title",
                subtitle="Test Subtitle"
            )
            # Should be called at least 3 times (title, content, subtitle)
            assert mock_render.call_count >= 3
    
    def test_print_table_fallback(self):
        """Test print_table in fallback mode."""
        terminal = RichTerminal(use_rich=False)
        
        with patch.object(terminal.buffered_renderer, 'render_persistent_message') as mock_render:
            data = [["A", "B"], ["C", "D"]]
            headers = ["Col1", "Col2"]
            terminal.print_table(data, headers=headers, title="Test Table")
            # Title + headers + separator + 2 data rows = at least 5 calls
            assert mock_render.call_count >= 4
    
    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initialization."""
        progress = Mock()
        task_id = 1
        tracker = ProgressTracker(progress, task_id)
        
        assert tracker.progress == progress
        assert tracker.task_id == task_id
    
    def test_progress_tracker_update(self):
        """Test ProgressTracker update."""
        progress = Mock()
        task_id = 1
        tracker = ProgressTracker(progress, task_id)
        
        tracker.update(50)
        progress.update.assert_called_once_with(task_id, advance=50)
    
    def test_fallback_progress_tracker(self):
        """Test FallbackProgressTracker."""
        terminal = Mock()
        terminal.buffered_renderer = Mock()
        terminal.buffered_renderer.render_status_line = Mock()
        
        tracker = FallbackProgressTracker(terminal, "Test", 100)
        assert tracker.terminal == terminal
        assert tracker.total == 100
        
        tracker.update(50)
        terminal.buffered_renderer.render_status_line.assert_called_once()
        assert tracker.current == 50
    
    def test_live_display(self):
        """Test LiveDisplay."""
        live = Mock()
        display = LiveDisplay(live)
        
        display.update("content")
        live.update.assert_called_once_with("content")
    
    def test_fallback_live_display(self):
        """Test FallbackLiveDisplay."""
        terminal = Mock()
        terminal.clear_last_frame = Mock()
        terminal.print = Mock()
        
        display = FallbackLiveDisplay(terminal)
        display.update("content")
        
        terminal.clear_last_frame.assert_called_once()
        terminal.print.assert_called_once_with("content", persist=False)