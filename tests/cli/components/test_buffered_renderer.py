import pytest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from collections import deque

from storm_checker.cli.components.buffered_renderer import (
    BufferedRenderer, 
    RenderMode, 
    BufferFrame,
    create_slideshow_renderer,
    create_interactive_renderer,
    demo_buffered_renderer
)


class TestBufferedRenderer:
    """Comprehensive tests for BufferedRenderer."""
    
    def test_initialization_basic(self):
        """Test basic initialization."""
        renderer = BufferedRenderer()
        assert isinstance(renderer, BufferedRenderer)
        assert isinstance(renderer.buffer, deque)
        assert renderer.buffer.maxlen == 1000
        assert renderer.enable_scroll_regions == True
        assert renderer.enable_mouse == False
        assert renderer.cursor_row == 0
        assert renderer.cursor_col == 0
        assert renderer.current_frame_id is None
        assert renderer.last_frame_height == 0
        
    def test_initialization_custom_params(self):
        """Test initialization with custom parameters."""
        renderer = BufferedRenderer(
            max_buffer_size=500,
            enable_scroll_regions=False,
            enable_mouse=True
        )
        assert renderer.buffer.maxlen == 500
        assert renderer.enable_scroll_regions == False
        assert renderer.enable_mouse == True
        
    @patch('os.get_terminal_size')
    def test_get_terminal_width_success(self, mock_get_size):
        """Test successful terminal width detection."""
        mock_get_size.return_value = Mock(columns=120, lines=30)
        renderer = BufferedRenderer()
        width = renderer._get_terminal_width()
        assert width == 120
        
    @patch('os.get_terminal_size')
    def test_get_terminal_width_large_fallback(self, mock_get_size):
        """Test terminal width capped at 120."""
        mock_get_size.return_value = Mock(columns=200, lines=30)
        renderer = BufferedRenderer()
        width = renderer._get_terminal_width()
        assert width == 120  # Should be capped
        
    @patch('os.get_terminal_size')
    def test_get_terminal_width_exception(self, mock_get_size):
        """Test terminal width fallback on exception."""
        mock_get_size.side_effect = OSError("No terminal")
        renderer = BufferedRenderer()
        width = renderer._get_terminal_width()
        assert width == 80  # Fallback value
        
    @patch('os.get_terminal_size')
    def test_get_terminal_height_success(self, mock_get_size):
        """Test successful terminal height detection."""
        mock_get_size.return_value = Mock(columns=80, lines=25)
        renderer = BufferedRenderer()
        height = renderer._get_terminal_height()
        assert height == 25
        
    @patch('os.get_terminal_size')
    def test_get_terminal_height_exception(self, mock_get_size):
        """Test terminal height fallback on exception."""
        mock_get_size.side_effect = OSError("No terminal")
        renderer = BufferedRenderer()
        height = renderer._get_terminal_height()
        assert height == 24  # Fallback value
        
    @patch('os.get_terminal_size')
    def test_update_terminal_size_changed(self, mock_get_size):
        """Test terminal size update when size changes."""
        # Initial size
        mock_get_size.return_value = Mock(columns=80, lines=24)
        renderer = BufferedRenderer()
        initial_width = renderer.terminal_width
        initial_height = renderer.terminal_height
        
        # Change size
        mock_get_size.return_value = Mock(columns=100, lines=30)
        changed = renderer._update_terminal_size()
        
        assert changed == True
        assert renderer.terminal_width != initial_width
        assert renderer.terminal_height != initial_height
        
    @patch('os.get_terminal_size')
    def test_update_terminal_size_unchanged(self, mock_get_size):
        """Test terminal size update when size unchanged."""
        mock_get_size.return_value = Mock(columns=80, lines=24)
        renderer = BufferedRenderer()
        
        # Same size
        changed = renderer._update_terminal_size()
        assert changed == False
        
    def test_strip_ansi(self):
        """Test ANSI escape code stripping."""
        renderer = BufferedRenderer()
        
        # Test with ANSI codes
        text_with_ansi = "\033[31mRed text\033[0m\033[1mBold\033[0m"
        clean_text = renderer._strip_ansi(text_with_ansi)
        assert clean_text == "Red textBold"
        
        # Test without ANSI codes
        plain_text = "Plain text"
        assert renderer._strip_ansi(plain_text) == plain_text
        
        # Test empty string
        assert renderer._strip_ansi("") == ""
        
    def test_get_cursor_position(self):
        """Test cursor position tracking."""
        renderer = BufferedRenderer()
        row, col = renderer._get_cursor_position()
        assert row == renderer.cursor_row
        assert col == renderer.cursor_col
        
    @patch('sys.stdout')
    def test_move_cursor_with_row_and_col(self, mock_stdout):
        """Test cursor movement with row and column."""
        renderer = BufferedRenderer()
        renderer._move_cursor(5, 10)
        
        mock_stdout.write.assert_called_with("\033[5;10H")
        assert renderer.cursor_row == 5
        assert renderer.cursor_col == 10
        
    @patch('sys.stdout')
    def test_move_cursor_with_row_only(self, mock_stdout):
        """Test cursor movement with row only."""
        renderer = BufferedRenderer()
        renderer._move_cursor(3)
        
        mock_stdout.write.assert_called_with("\033[3H")
        assert renderer.cursor_row == 3
        assert renderer.cursor_col == 0
        
    @patch('sys.stdout')
    def test_move_cursor_home(self, mock_stdout):
        """Test cursor movement to home position."""
        renderer = BufferedRenderer()
        renderer._move_cursor(0)
        
        mock_stdout.write.assert_called_with("\033[H")
        assert renderer.cursor_row == 0
        assert renderer.cursor_col == 0
        
    @patch('sys.stdout')
    def test_move_cursor_relative_down(self, mock_stdout):
        """Test relative cursor movement down."""
        renderer = BufferedRenderer()
        renderer.cursor_row = 5
        renderer._move_cursor_relative(rows=3)
        
        mock_stdout.write.assert_called_with("\033[3B")
        assert renderer.cursor_row == 8
        
    @patch('sys.stdout')
    def test_move_cursor_relative_up(self, mock_stdout):
        """Test relative cursor movement up."""
        renderer = BufferedRenderer()
        renderer.cursor_row = 5
        renderer._move_cursor_relative(rows=-2)
        
        mock_stdout.write.assert_called_with("\033[2A")
        assert renderer.cursor_row == 3
        
    @patch('sys.stdout')
    def test_move_cursor_relative_right(self, mock_stdout):
        """Test relative cursor movement right."""
        renderer = BufferedRenderer()
        renderer.cursor_col = 5
        renderer._move_cursor_relative(cols=4)
        
        mock_stdout.write.assert_called_with("\033[4C")
        assert renderer.cursor_col == 9
        
    @patch('sys.stdout')
    def test_move_cursor_relative_left(self, mock_stdout):
        """Test relative cursor movement left."""
        renderer = BufferedRenderer()
        renderer.cursor_col = 5
        renderer._move_cursor_relative(cols=-3)
        
        mock_stdout.write.assert_called_with("\033[3D")
        assert renderer.cursor_col == 2
        
    @patch('sys.stdout')
    def test_clear_lines_single(self, mock_stdout):
        """Test clearing a single line."""
        renderer = BufferedRenderer()
        renderer._clear_lines(1)
        
        mock_stdout.write.assert_called_with("\033[K")
        
    @patch('sys.stdout')
    def test_clear_lines_multiple(self, mock_stdout):
        """Test clearing multiple lines."""
        renderer = BufferedRenderer()
        mock_stdout.reset_mock()  # Clear initialization calls
        
        renderer._clear_lines(3)
        
        # Should call write 5 times: K, B, K, B, K
        assert mock_stdout.write.call_count == 5
        
        # Get just the calls we care about (after initialization)
        calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        
        # Should contain clear and move commands
        assert "\033[K" in calls  # Clear line command appears
        assert "\033[B" in calls  # Move down command appears
            
    @patch('sys.stdout')
    def test_setup_scroll_region(self, mock_stdout):
        """Test scroll region setup."""
        renderer = BufferedRenderer(enable_scroll_regions=True)
        renderer._setup_scroll_region(5, 20)
        
        mock_stdout.write.assert_called_with("\033[5;20r")
        
    @patch('sys.stdout')
    def test_setup_scroll_region_disabled(self, mock_stdout):
        """Test scroll region when disabled."""
        renderer = BufferedRenderer(enable_scroll_regions=False)
        renderer._setup_scroll_region(5, 20)
        
        # Should not write anything when disabled
        assert not any("\033[5;20r" in str(call) for call in mock_stdout.write.call_args_list)
        
    @patch('sys.stdout')
    def test_reset_scroll_region(self, mock_stdout):
        """Test scroll region reset."""
        renderer = BufferedRenderer(enable_scroll_regions=True)
        renderer._reset_scroll_region()
        
        mock_stdout.write.assert_called_with("\033[r")
        
    @patch('sys.stdout')
    def test_reset_scroll_region_disabled(self, mock_stdout):
        """Test scroll region reset when disabled."""
        renderer = BufferedRenderer(enable_scroll_regions=False)
        renderer._reset_scroll_region()
        
        # Should not write anything when disabled
        assert not any("\033[r" in str(call) for call in mock_stdout.write.call_args_list)
        
    @patch('sys.stdout')
    def test_initialize_terminal_no_mouse(self, mock_stdout):
        """Test terminal initialization without mouse support."""
        renderer = BufferedRenderer(enable_mouse=False)
        
        # Check if CURSOR_HIDE was called
        calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        assert "\033[?25l" in calls  # Hide cursor
        assert not any("1000h" in call for call in calls)  # No mouse
        
    @patch('sys.stdout')
    def test_initialize_terminal_with_mouse(self, mock_stdout):
        """Test terminal initialization with mouse support."""
        renderer = BufferedRenderer(enable_mouse=True)
        
        # Check if CURSOR_HIDE and mouse enable were called
        calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        assert "\033[?25l" in calls  # Hide cursor
        assert "\033[?1000h" in calls  # Enable mouse
        
    @patch('sys.stdout')
    def test_cleanup_no_mouse(self, mock_stdout):
        """Test terminal cleanup without mouse support."""
        renderer = BufferedRenderer(enable_mouse=False)
        mock_stdout.reset_mock()  # Clear initialization calls
        
        renderer.cleanup()
        
        calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        assert "\033[?25h" in calls  # Show cursor
        assert not any("1000l" in call for call in calls)  # No mouse disable
        
    @patch('sys.stdout')
    def test_cleanup_with_mouse(self, mock_stdout):
        """Test terminal cleanup with mouse support."""
        renderer = BufferedRenderer(enable_mouse=True)
        mock_stdout.reset_mock()  # Clear initialization calls
        
        renderer.cleanup()
        
        calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        assert "\033[?25h" in calls  # Show cursor
        assert "\033[?1000l" in calls  # Disable mouse


class TestRenderModes:
    """Test all render modes comprehensively."""
    
    @patch('sys.stdout')
    @patch('builtins.print')
    def test_render_append_mode(self, mock_print, mock_stdout):
        """Test APPEND render mode."""
        renderer = BufferedRenderer()
        content = ["Line 1", "Line 2", "Line 3"]
        
        renderer.render_frame(content, RenderMode.APPEND, "test_frame")
        
        # Should print each line
        assert mock_print.call_count == 3
        mock_print.assert_any_call("Line 1")
        mock_print.assert_any_call("Line 2")
        mock_print.assert_any_call("Line 3")
        
        # Should update buffer
        assert len(renderer.buffer) == 1
        assert renderer.buffer[0].content == content
        assert renderer.buffer[0].mode == RenderMode.APPEND
        assert renderer.buffer[0].frame_id == "test_frame"
        assert renderer.current_frame_id == "test_frame"
        assert renderer.last_frame_height == 3
        
    @patch('sys.stdout')
    @patch('builtins.print')
    def test_render_replace_last_mode(self, mock_print, mock_stdout):
        """Test REPLACE_LAST render mode."""
        renderer = BufferedRenderer()
        
        # First render something
        first_content = ["First line", "Second line"]
        renderer.render_frame(first_content, RenderMode.APPEND)
        mock_print.reset_mock()
        mock_stdout.reset_mock()
        
        # Now replace it
        new_content = ["New line 1", "New line 2", "New line 3"]
        renderer.render_frame(new_content, RenderMode.REPLACE_LAST)
        
        # Should move cursor up and clear lines
        calls = [str(call) for call in mock_stdout.write.call_args_list]
        assert any("A" in call for call in calls)  # Move up
        assert any("K" in call for call in calls)  # Clear line
        
        # Should print new content
        assert mock_print.call_count == 3
        mock_print.assert_any_call("New line 1")
        mock_print.assert_any_call("New line 2")
        mock_print.assert_any_call("New line 3")
        
    @patch('sys.stdout')
    def test_render_overlay_mode(self, mock_stdout):
        """Test OVERLAY render mode."""
        renderer = BufferedRenderer()
        renderer.cursor_row = 5
        renderer.cursor_col = 10
        
        content = ["Overlay line 1", "Overlay line 2"]
        renderer.render_frame(content, RenderMode.OVERLAY)
        
        # Should move cursor and clear lines
        calls = [str(call) for call in mock_stdout.write.call_args_list]
        position_calls = [call for call in calls if "H" in str(call)]
        clear_calls = [call for call in calls if "K" in str(call)]
        
        assert len(position_calls) >= 2  # Should position cursor for each line
        assert len(clear_calls) == 2     # Should clear each line
        
        # Should update cursor position
        assert renderer.cursor_row == 7  # 5 + 2 lines
        
    @patch('sys.stdout')
    @patch('builtins.print')
    def test_render_scroll_region_mode_enabled(self, mock_print, mock_stdout):
        """Test SCROLL_REGION render mode when enabled."""
        renderer = BufferedRenderer(enable_scroll_regions=True)
        renderer.cursor_row = 5
        renderer.terminal_height = 30
        
        content = ["Scroll line 1", "Scroll line 2"]
        renderer.render_frame(content, RenderMode.SCROLL_REGION)
        
        # Should set up scroll region
        calls = [str(call) for call in mock_stdout.write.call_args_list]
        assert any("r" in call for call in calls)  # Scroll region setup/reset
        
        # Should print content
        assert mock_print.call_count == 2
        
    @patch('sys.stdout')
    @patch('builtins.print')
    def test_render_scroll_region_mode_disabled(self, mock_print, mock_stdout):
        """Test SCROLL_REGION render mode when disabled (falls back to APPEND)."""
        renderer = BufferedRenderer(enable_scroll_regions=False)
        
        content = ["Scroll line 1", "Scroll line 2"]
        renderer.render_frame(content, RenderMode.SCROLL_REGION)
        
        # Should fall back to append mode (just print)
        assert mock_print.call_count == 2
        mock_print.assert_any_call("Scroll line 1")
        mock_print.assert_any_call("Scroll line 2")
        
    @patch('sys.stdout')
    def test_render_frame_auto_id_generation(self, mock_stdout):
        """Test automatic frame ID generation."""
        renderer = BufferedRenderer()
        content = ["Test line"]
        
        renderer.render_frame(content)  # No frame_id provided
        
        # Should generate an ID
        assert renderer.current_frame_id is not None
        assert renderer.current_frame_id.startswith("frame_")
        assert len(renderer.buffer) == 1
        assert renderer.buffer[0].frame_id == renderer.current_frame_id
        
    @patch('sys.stdout')
    def test_render_frame_updates_terminal_size(self, mock_stdout):
        """Test that render_frame updates terminal size."""
        with patch.object(BufferedRenderer, '_update_terminal_size') as mock_update:
            renderer = BufferedRenderer()
            content = ["Test line"]
            
            renderer.render_frame(content)
            
            mock_update.assert_called_once()


class TestSpecializedMethods:
    """Test specialized rendering methods."""
    
    @patch('sys.stdout')
    def test_render_slideshow_frame_replace(self, mock_stdout):
        """Test slideshow frame rendering with replacement."""
        renderer = BufferedRenderer()
        content = "Line 1\nLine 2\nLine 3"
        
        with patch.object(renderer, 'render_frame') as mock_render:
            renderer.render_slideshow_frame(content, replace_previous=True, frame_id="slide1")
            
            mock_render.assert_called_once_with(
                ["Line 1", "Line 2", "Line 3"],
                RenderMode.REPLACE_LAST,
                "slide1"
            )
            
    @patch('sys.stdout')
    def test_render_slideshow_frame_append(self, mock_stdout):
        """Test slideshow frame rendering with append."""
        renderer = BufferedRenderer()
        content = "Single line"
        
        with patch.object(renderer, 'render_frame') as mock_render:
            renderer.render_slideshow_frame(content, replace_previous=False)
            
            mock_render.assert_called_once_with(
                ["Single line"],
                RenderMode.APPEND,
                None
            )
            
    @patch('sys.stdout')
    def test_render_persistent_message(self, mock_stdout):
        """Test persistent message rendering."""
        renderer = BufferedRenderer()
        
        with patch.object(renderer, 'render_frame') as mock_render:
            renderer.render_persistent_message("Test message", "success")
            
            # Should call render_frame with formatted message
            mock_render.assert_called_once()
            args = mock_render.call_args[0]
            assert len(args[0]) == 1  # One line
            assert "Test message" in args[0][0]
            assert args[1] == RenderMode.APPEND
            
    @patch('sys.stdout')
    def test_render_persistent_message_default_style(self, mock_stdout):
        """Test persistent message with default style."""
        renderer = BufferedRenderer()
        
        with patch.object(renderer, 'render_frame') as mock_render:
            renderer.render_persistent_message("Test message")
            
            mock_render.assert_called_once()
            
    @patch('sys.stdout')
    def test_render_status_line_replace(self, mock_stdout):
        """Test status line rendering with replacement."""
        renderer = BufferedRenderer()
        
        with patch.object(renderer, 'render_frame') as mock_render:
            renderer.render_status_line("Status update", replace=True)
            
            mock_render.assert_called_once_with(
                ["\033[38;2;88;122;132mStatus update\033[0m"],
                RenderMode.REPLACE_LAST,
                "status_line"
            )
            
    @patch('sys.stdout')
    def test_render_status_line_append(self, mock_stdout):
        """Test status line rendering with append."""
        renderer = BufferedRenderer()
        
        with patch.object(renderer, 'render_frame') as mock_render:
            renderer.render_status_line("Status update", replace=False)
            
            mock_render.assert_called_once_with(
                ["\033[38;2;88;122;132mStatus update\033[0m"],
                RenderMode.APPEND,
                "status_line"
            )


class TestBufferManagement:
    """Test buffer management functionality."""
    
    def test_get_buffer_history(self):
        """Test buffer history retrieval."""
        renderer = BufferedRenderer()
        
        # Add some frames
        for i in range(5):
            content = [f"Frame {i}"]
            renderer.render_frame(content, frame_id=f"frame_{i}")
            
        # Get recent history
        history = renderer.get_buffer_history(3)
        assert len(history) == 3
        assert history[0].frame_id == "frame_2"
        assert history[1].frame_id == "frame_3"
        assert history[2].frame_id == "frame_4"
        
        # Get all history
        all_history = renderer.get_buffer_history(10)
        assert len(all_history) == 5
        
    def test_clear_buffer(self):
        """Test buffer clearing."""
        renderer = BufferedRenderer()
        
        # Add some frames
        renderer.render_frame(["Test"], frame_id="test")
        assert len(renderer.buffer) == 1
        assert renderer.current_frame_id == "test"
        assert renderer.last_frame_height == 1
        
        # Clear buffer
        renderer.clear_buffer()
        assert len(renderer.buffer) == 0
        assert renderer.current_frame_id is None
        assert renderer.last_frame_height == 0
        
    def test_buffer_max_size(self):
        """Test buffer maximum size enforcement."""
        renderer = BufferedRenderer(max_buffer_size=3)
        
        # Add more frames than max size
        for i in range(5):
            renderer.render_frame([f"Frame {i}"], frame_id=f"frame_{i}")
            
        # Should only keep last 3
        assert len(renderer.buffer) == 3
        assert renderer.buffer[0].frame_id == "frame_2"
        assert renderer.buffer[1].frame_id == "frame_3"
        assert renderer.buffer[2].frame_id == "frame_4"


class TestCursorManagement:
    """Test cursor save/restore functionality."""
    
    @patch('sys.stdout')
    def test_save_cursor(self, mock_stdout):
        """Test cursor position saving."""
        renderer = BufferedRenderer()
        renderer.save_cursor()
        
        mock_stdout.write.assert_called_with("\033[s")
        
    @patch('sys.stdout')
    def test_restore_cursor(self, mock_stdout):
        """Test cursor position restoration."""
        renderer = BufferedRenderer()
        renderer.restore_cursor()
        
        mock_stdout.write.assert_called_with("\033[u")


class TestContextManager:
    """Test context manager functionality."""
    
    @patch('sys.stdout')
    def test_context_manager_entry(self, mock_stdout):
        """Test context manager entry."""
        with BufferedRenderer() as renderer:
            assert isinstance(renderer, BufferedRenderer)
            
    @patch('sys.stdout')
    def test_context_manager_exit_normal(self, mock_stdout):
        """Test context manager exit without exception."""
        renderer = BufferedRenderer()
        mock_stdout.reset_mock()
        
        # Manually call __exit__ 
        renderer.__exit__(None, None, None)
        
        # Should call cleanup
        calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        assert "\033[?25h" in calls  # Show cursor
        
    @patch('sys.stdout')
    def test_context_manager_exit_with_exception(self, mock_stdout):
        """Test context manager exit with exception."""
        renderer = BufferedRenderer()
        mock_stdout.reset_mock()
        
        # Manually call __exit__ with exception info
        renderer.__exit__(ValueError, ValueError("test"), None)
        
        # Should still call cleanup
        calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        assert "\033[?25h" in calls  # Show cursor


class TestConvenienceFunctions:
    """Test convenience factory functions."""
    
    @patch('sys.stdout')
    def test_create_slideshow_renderer(self, mock_stdout):
        """Test slideshow renderer creation."""
        renderer = create_slideshow_renderer()
        
        assert isinstance(renderer, BufferedRenderer)
        assert renderer.buffer.maxlen == 100
        assert renderer.enable_scroll_regions == True
        assert renderer.enable_mouse == False
        
    @patch('sys.stdout')
    def test_create_interactive_renderer(self, mock_stdout):
        """Test interactive renderer creation."""
        renderer = create_interactive_renderer()
        
        assert isinstance(renderer, BufferedRenderer)
        assert renderer.buffer.maxlen == 500
        assert renderer.enable_scroll_regions == True
        assert renderer.enable_mouse == True


class TestBufferFrame:
    """Test BufferFrame dataclass."""
    
    def test_buffer_frame_creation(self):
        """Test BufferFrame creation."""
        content = ["Line 1", "Line 2"]
        frame = BufferFrame(
            content=content,
            mode=RenderMode.APPEND,
            height=2,
            timestamp=123.456,
            frame_id="test_frame"
        )
        
        assert frame.content == content
        assert frame.mode == RenderMode.APPEND
        assert frame.height == 2
        assert frame.timestamp == 123.456
        assert frame.frame_id == "test_frame"


class TestRenderModeEnum:
    """Test RenderMode enum."""
    
    def test_render_mode_values(self):
        """Test RenderMode enum values."""
        assert RenderMode.APPEND.value == "append"
        assert RenderMode.REPLACE_LAST.value == "replace"
        assert RenderMode.OVERLAY.value == "overlay"
        assert RenderMode.SCROLL_REGION.value == "scroll"


class TestDemoFunction:
    """Test the demo function."""
    
    @patch('time.sleep')
    @patch('sys.stdout')
    def test_demo_buffered_renderer(self, mock_stdout, mock_sleep):
        """Test the demo function runs without error."""
        # This tests that the demo function executes all code paths
        demo_buffered_renderer()
        
        # Verify that the demo ran (some output was written)
        assert mock_stdout.write.called
        
        # Verify sleep was called (demo has timing delays)
        assert mock_sleep.called
