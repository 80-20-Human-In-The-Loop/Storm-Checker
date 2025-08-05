#!/usr/bin/env python3
"""
Buffered Terminal Renderer
==========================
World-class terminal output system that maintains scrollable history
while providing smooth, non-destructive updates.
"""

import os
import sys
import re
from typing import List, Optional, Tuple, Dict, Any
from collections import deque
from dataclasses import dataclass
from enum import Enum

from storm_checker.cli.colors import THEME, RESET, CURSOR_HIDE, CURSOR_SHOW


class RenderMode(Enum):
    """Different rendering modes for terminal output."""
    APPEND = "append"          # Add to terminal history (default)
    REPLACE_LAST = "replace"   # Replace the last rendered content
    OVERLAY = "overlay"        # Overlay content at current position
    SCROLL_REGION = "scroll"   # Use terminal scroll regions


@dataclass
class BufferFrame:
    """Represents a frame of content in the terminal buffer."""
    content: List[str]
    mode: RenderMode
    height: int
    timestamp: float
    frame_id: str


class BufferedRenderer:
    """
    World-class terminal renderer that maintains scrollable history.
    
    Features:
    - Persistent terminal output (users can scroll up)
    - Smart cursor positioning (no screen clearing)
    - Scroll regions for contained content
    - Buffer management for large output
    - Terminal capability detection
    """
    
    def __init__(
        self,
        max_buffer_size: int = 1000,
        enable_scroll_regions: bool = True,
        enable_mouse: bool = False
    ):
        """
        Initialize the buffered renderer.
        
        Args:
            max_buffer_size: Maximum number of frames to keep in buffer
            enable_scroll_regions: Whether to use terminal scroll regions
            enable_mouse: Whether to enable mouse support
        """
        self.buffer: deque[BufferFrame] = deque(maxlen=max_buffer_size)
        self.enable_scroll_regions = enable_scroll_regions
        self.enable_mouse = enable_mouse
        
        # Terminal state
        self.terminal_width = self._get_terminal_width()
        self.terminal_height = self._get_terminal_height()
        self.cursor_row = 0
        self.cursor_col = 0
        
        # Frame tracking
        self.current_frame_id: Optional[str] = None
        self.last_frame_height = 0
        
        # Initialize terminal
        self._initialize_terminal()
        
    def _initialize_terminal(self) -> None:
        """Initialize terminal for optimal rendering."""
        # Hide cursor during initialization
        sys.stdout.write(CURSOR_HIDE)
        
        # Enable alternative buffer if needed (commented out for now)
        # sys.stdout.write("\033[?1049h")  # Enable alternative screen buffer
        
        # Enable mouse support if requested
        if self.enable_mouse:
            sys.stdout.write("\033[?1000h")  # Enable mouse reporting
            
        sys.stdout.flush()
        
    def cleanup(self) -> None:
        """Cleanup terminal state."""
        # Disable mouse support
        if self.enable_mouse:
            sys.stdout.write("\033[?1000l")
            
        # Restore cursor
        sys.stdout.write(CURSOR_SHOW)
        
        # Disable alternative buffer if we enabled it
        # sys.stdout.write("\033[?1049l")
        
        sys.stdout.flush()
        
    def _get_terminal_width(self) -> int:
        """Get terminal width with fallback."""
        try:
            return min(os.get_terminal_size().columns, 120)  # Cap for readability
        except:
            return 80
            
    def _get_terminal_height(self) -> int:
        """Get terminal height with fallback."""
        try:
            return os.get_terminal_size().lines
        except:
            return 24
            
    def _update_terminal_size(self) -> bool:
        """Update terminal size and return True if changed."""
        old_width, old_height = self.terminal_width, self.terminal_height
        self.terminal_width = self._get_terminal_width()
        self.terminal_height = self._get_terminal_height()
        return (old_width != self.terminal_width or 
                old_height != self.terminal_height)
                
    def _strip_ansi(self, text: str) -> str:
        """Strip ANSI escape codes from text for length calculation."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
        
    def _get_cursor_position(self) -> Tuple[int, int]:
        """Get current cursor position (row, col)."""
        # This is complex in practice and not always reliable
        # For now, we'll track position ourselves
        return self.cursor_row, self.cursor_col
        
    def _move_cursor(self, row: int, col: int = 0) -> None:
        """Move cursor to specific position."""
        if row > 0 and col > 0:
            sys.stdout.write(f"\033[{row};{col}H")
        elif row > 0:
            sys.stdout.write(f"\033[{row}H")
        else:
            sys.stdout.write("\033[H")  # Home position
        self.cursor_row, self.cursor_col = row, col
        
    def _move_cursor_relative(self, rows: int = 0, cols: int = 0) -> None:
        """Move cursor relative to current position."""
        if rows > 0:
            sys.stdout.write(f"\033[{rows}B")  # Down
        elif rows < 0:
            sys.stdout.write(f"\033[{abs(rows)}A")  # Up
            
        if cols > 0:
            sys.stdout.write(f"\033[{cols}C")  # Right
        elif cols < 0:
            sys.stdout.write(f"\033[{abs(cols)}D")  # Left
            
        self.cursor_row += rows
        self.cursor_col += cols
        
    def _clear_lines(self, num_lines: int) -> None:
        """Clear the next num_lines from current position."""
        for i in range(num_lines):
            sys.stdout.write("\033[K")  # Clear line
            if i < num_lines - 1:
                sys.stdout.write("\033[B")  # Move down
                
    def _setup_scroll_region(self, top: int, bottom: int) -> None:
        """Set up a scroll region between top and bottom lines."""
        if self.enable_scroll_regions:
            sys.stdout.write(f"\033[{top};{bottom}r")
            
    def _reset_scroll_region(self) -> None:
        """Reset scroll region to full screen."""
        if self.enable_scroll_regions:
            sys.stdout.write("\033[r")
            
    def render_frame(
        self,
        content: List[str],
        mode: RenderMode = RenderMode.APPEND,
        frame_id: Optional[str] = None
    ) -> None:
        """
        Render a frame of content to the terminal.
        
        Args:
            content: List of lines to render
            mode: How to render the content
            frame_id: Unique identifier for this frame
        """
        import time
        
        # Update terminal size if needed
        self._update_terminal_size()
        
        # Generate frame ID if not provided
        if frame_id is None:
            frame_id = f"frame_{len(self.buffer)}_{time.time()}"
            
        # Create buffer frame
        frame = BufferFrame(
            content=content.copy(),
            mode=mode,
            height=len(content),
            timestamp=time.time(),
            frame_id=frame_id
        )
        
        # Handle different render modes
        if mode == RenderMode.APPEND:
            self._render_append(frame)
        elif mode == RenderMode.REPLACE_LAST:
            self._render_replace_last(frame)
        elif mode == RenderMode.OVERLAY:
            self._render_overlay(frame)
        elif mode == RenderMode.SCROLL_REGION:
            self._render_scroll_region(frame)
            
        # Add to buffer
        self.buffer.append(frame)
        self.current_frame_id = frame_id
        self.last_frame_height = frame.height
        
        # Flush output
        sys.stdout.flush()
        
    def _render_append(self, frame: BufferFrame) -> None:
        """Render frame by appending to terminal output."""
        # Simply print each line - this preserves terminal history
        for line in frame.content:
            print(line)
            self.cursor_row += 1
            
    def _render_replace_last(self, frame: BufferFrame) -> None:
        """Replace the last rendered frame with new content."""
        if self.last_frame_height > 0:
            # Move cursor up to start of last frame
            self._move_cursor_relative(rows=-self.last_frame_height)
            # Clear the lines
            self._clear_lines(self.last_frame_height)
            # Move cursor back to start
            self._move_cursor_relative(rows=-self.last_frame_height)
            
        # Render new content
        for line in frame.content:
            print(line)
            self.cursor_row += 1
            
    def _render_overlay(self, frame: BufferFrame) -> None:
        """Render frame as overlay at current position."""
        current_row, current_col = self.cursor_row, self.cursor_col
        
        for i, line in enumerate(frame.content):
            self._move_cursor(current_row + i, current_col)
            sys.stdout.write("\033[K")  # Clear line
            sys.stdout.write(line)
            
        # Move cursor to end of overlay
        self.cursor_row = current_row + len(frame.content)
        
    def _render_scroll_region(self, frame: BufferFrame) -> None:
        """Render frame within a scroll region."""
        if not self.enable_scroll_regions:
            self._render_append(frame)
            return
            
        # Set up scroll region (reserve space for frame)
        region_start = max(1, self.cursor_row)
        region_end = min(self.terminal_height - 2, region_start + frame.height)
        
        self._setup_scroll_region(region_start, region_end)
        
        # Move to scroll region and render
        self._move_cursor(region_start)
        for line in frame.content:
            print(line)
            
        # Reset scroll region
        self._reset_scroll_region()
        
        # Update cursor position
        self.cursor_row = region_end + 1
        
    def render_slideshow_frame(
        self,
        content: str,
        replace_previous: bool = True,
        frame_id: Optional[str] = None
    ) -> None:
        """
        Specialized method for rendering slideshow content.
        
        Args:
            content: Complete slideshow content as string
            replace_previous: Whether to replace previous slideshow frame
            frame_id: Frame identifier
        """
        lines = content.split('\n')
        
        mode = RenderMode.REPLACE_LAST if replace_previous else RenderMode.APPEND
        self.render_frame(lines, mode, frame_id)
        
    def render_persistent_message(
        self,
        message: str,
        style: str = "info"
    ) -> None:
        """
        Render a message that persists in terminal history.
        
        Args:
            message: Message to display
            style: Style theme to use
        """
        color = THEME.get(style, THEME['info'])
        formatted_message = f"{color}{message}{RESET}"
        
        self.render_frame([formatted_message], RenderMode.APPEND)
        
    def render_status_line(
        self,
        status: str,
        replace: bool = True
    ) -> None:
        """
        Render a status line that can be updated in place.
        
        Args:
            status: Status message
            replace: Whether to replace previous status
        """
        formatted_status = f"{THEME['info']}{status}{RESET}"
        mode = RenderMode.REPLACE_LAST if replace else RenderMode.APPEND
        
        self.render_frame([formatted_status], mode, "status_line")
        
    def get_buffer_history(self, num_frames: int = 10) -> List[BufferFrame]:
        """Get recent buffer history."""
        return list(self.buffer)[-num_frames:]
        
    def clear_buffer(self) -> None:
        """Clear the internal buffer (doesn't affect terminal display)."""
        self.buffer.clear()
        self.current_frame_id = None
        self.last_frame_height = 0
        
    def save_cursor(self) -> None:
        """Save current cursor position."""
        sys.stdout.write("\033[s")
        
    def restore_cursor(self) -> None:
        """Restore previously saved cursor position."""
        sys.stdout.write("\033[u")
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


# Convenience functions for common use cases
def create_slideshow_renderer() -> BufferedRenderer:
    """Create a renderer optimized for slideshow content."""
    return BufferedRenderer(
        max_buffer_size=100,
        enable_scroll_regions=True,
        enable_mouse=False
    )


def create_interactive_renderer() -> BufferedRenderer:
    """Create a renderer optimized for interactive content."""
    return BufferedRenderer(
        max_buffer_size=500,
        enable_scroll_regions=True,
        enable_mouse=True
    )


# Demo function
def demo_buffered_renderer():
    """Demonstrate the buffered renderer capabilities."""
    import time
    
    with BufferedRenderer() as renderer:
        # Show persistent messages
        renderer.render_persistent_message("=== Buffered Renderer Demo ===", "primary")
        renderer.render_persistent_message("This message will stay in your terminal history!", "success")
        
        time.sleep(1)
        
        # Show status updates
        for i in range(5):
            renderer.render_status_line(f"Processing step {i+1}/5...", replace=True)
            time.sleep(0.5)
            
        renderer.render_persistent_message("✅ All steps completed!", "success")
        
        # Show frame replacement
        renderer.render_persistent_message("\n--- Frame Replacement Demo ---", "primary")
        
        demo_content = [
            "This content will be replaced...",
            "Line 2 of temporary content",
            "Line 3 of temporary content"
        ]
        
        renderer.render_frame(demo_content, RenderMode.APPEND, "demo_frame")
        time.sleep(2)
        
        new_content = [
            "✨ This content replaced the previous frame!",
            "The old content is gone, but messages above remain",
            "Users can still scroll up to see history"
        ]
        
        renderer.render_frame(new_content, RenderMode.REPLACE_LAST, "demo_frame_new")
        
        renderer.render_persistent_message("\n🎉 Demo complete! Check your terminal history.", "learn")


if __name__ == "__main__":
    demo_buffered_renderer()