#!/usr/bin/env python3
"""
Progress Bar Component for Storm-Checker
========================================
Beautiful progress indicators for tutorials and learning tracking.
"""

from typing import Optional, Tuple
import math

# Import our color system
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from cli.colors import THEME, PALETTE, RESET, BOLD


class ProgressBar:
    """Create beautiful progress bars for CLI."""
    
    # Progress bar styles
    STYLES = {
        "blocks": {
            "empty": "░",
            "filled": "█",
            "partial": ["▏", "▎", "▍", "▌", "▋", "▊", "▉"],
        },
        "dots": {
            "empty": "○",
            "filled": "●",
            "partial": ["◔", "◑", "◕"],
        },
        "arrows": {
            "empty": "─",
            "filled": "━",
            "partial": ["╸"],
        },
        "squares": {
            "empty": "▱",
            "filled": "▰",
            "partial": ["▰"],
        },
        "lines": {
            "empty": "╌",
            "filled": "─",
            "partial": ["╴"],
        }
    }
    
    def __init__(
        self,
        width: int = 20,
        style: str = "blocks",
        color_empty: str = "text_muted",
        color_filled: str = "primary",
        color_text: str = "info",
        show_percentage: bool = True,
        show_fraction: bool = False
    ):
        """
        Initialize progress bar.
        
        Args:
            width: Width of the bar in characters
            style: Style name from STYLES
            color_empty: Color for empty portion
            color_filled: Color for filled portion
            color_text: Color for text labels
            show_percentage: Show percentage text
            show_fraction: Show fraction (e.g., 3/10)
        """
        self.width = width
        self.style = self.STYLES.get(style, self.STYLES["blocks"])
        self.color_empty = THEME.get(color_empty, "")
        self.color_filled = THEME.get(color_filled, "")
        self.color_text = THEME.get(color_text, "")
        self.show_percentage = show_percentage
        self.show_fraction = show_fraction
        
    def render(
        self,
        current: float,
        total: float,
        label: Optional[str] = None,
        suffix: Optional[str] = None
    ) -> str:
        """
        Render the progress bar.
        
        Args:
            current: Current progress value
            total: Total/maximum value
            label: Optional label before the bar
            suffix: Optional text after the bar
            
        Returns:
            Formatted progress bar string
        """
        if total == 0:
            percentage = 0
        else:
            percentage = min(100, (current / total) * 100)
            
        # Calculate filled width
        filled_width = (percentage / 100) * self.width
        filled_blocks = int(filled_width)
        partial_block = filled_width - filled_blocks
        
        # Build the bar
        bar_parts = []
        
        # Filled blocks
        if filled_blocks > 0:
            bar_parts.append(
                f"{self.color_filled}{self.style['filled'] * filled_blocks}{RESET}"
            )
            
        # Partial block
        if partial_block > 0 and filled_blocks < self.width:
            partial_index = int(partial_block * len(self.style['partial']))
            partial_char = self.style['partial'][min(partial_index, len(self.style['partial']) - 1)]
            bar_parts.append(
                f"{self.color_filled}{partial_char}{RESET}"
            )
            filled_blocks += 1
            
        # Empty blocks
        empty_blocks = self.width - filled_blocks
        if empty_blocks > 0:
            bar_parts.append(
                f"{self.color_empty}{self.style['empty'] * empty_blocks}{RESET}"
            )
            
        bar = "".join(bar_parts)
        
        # Build the complete line
        parts = []
        
        if label:
            parts.append(f"{self.color_text}{label}{RESET}")
            
        parts.append(f"[{bar}]")
        
        if self.show_percentage:
            parts.append(f"{self.color_text}{percentage:3.0f}%{RESET}")
            
        if self.show_fraction:
            parts.append(f"{self.color_text}{int(current)}/{int(total)}{RESET}")
            
        if suffix:
            parts.append(f"{self.color_text}{suffix}{RESET}")
            
        return " ".join(parts)
        
    def render_segmented(
        self,
        segments: list[Tuple[float, str]],
        current: float,
        label: Optional[str] = None
    ) -> str:
        """
        Render a segmented progress bar with different sections.
        
        Args:
            segments: List of (value, color_name) tuples
            current: Current position in the bar
            label: Optional label
            
        Returns:
            Formatted segmented progress bar
        """
        total = sum(value for value, _ in segments)
        if total == 0:
            return self.render(0, 1, label)
            
        parts = []
        if label:
            parts.append(f"{self.color_text}{label}{RESET}")
            
        parts.append("[")
        
        position = 0
        for value, color_name in segments:
            segment_width = int((value / total) * self.width)
            if segment_width > 0:
                color = THEME.get(color_name, "")
                
                # Check if current position is in this segment
                if position <= current < position + value:
                    # Partially filled segment
                    filled = int(((current - position) / value) * segment_width)
                    empty = segment_width - filled
                    
                    if filled > 0:
                        parts.append(f"{color}{self.style['filled'] * filled}{RESET}")
                    if empty > 0:
                        parts.append(f"{self.color_empty}{self.style['empty'] * empty}{RESET}")
                elif current >= position + value:
                    # Fully filled segment
                    parts.append(f"{color}{self.style['filled'] * segment_width}{RESET}")
                else:
                    # Empty segment
                    parts.append(f"{self.color_empty}{self.style['empty'] * segment_width}{RESET}")
                    
            position += value
            
        parts.append("]")
        
        if self.show_percentage:
            percentage = (current / total) * 100
            parts.append(f"{self.color_text}{percentage:3.0f}%{RESET}")
            
        return " ".join(parts)


class SpinnerBar:
    """Animated spinner/loading indicator."""
    
    SPINNERS = {
        "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["-", "\\", "|", "/"],
        "circle": ["◐", "◓", "◑", "◒"],
        "bounce": ["⠁", "⠂", "⠄", "⠂"],
        "blocks": ["▖", "▘", "▝", "▗"],
    }
    
    def __init__(self, style: str = "dots", color: str = "primary"):
        """Initialize spinner."""
        self.frames = self.SPINNERS.get(style, self.SPINNERS["dots"])
        self.color = THEME.get(color, "")
        self.current_frame = 0
        
    def next(self) -> str:
        """Get next frame of the spinner."""
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return f"{self.color}{frame}{RESET}"


def demo():
    """Demo various progress bar styles."""
    import time
    
    print("\n=== Storm-Checker Progress Bar Demo ===\n")
    
    # Basic progress bars
    print("Basic Progress Bars:")
    styles = ["blocks", "dots", "arrows", "squares", "lines"]
    
    for style in styles:
        bar = ProgressBar(width=30, style=style, color_filled="success")
        print(f"{style:10}", bar.render(7, 10))
    
    print("\nAnimated Progress:")
    bar = ProgressBar(width=40, color_filled="learn", show_fraction=True)
    for i in range(0, 101, 5):
        print(f"\r{bar.render(i, 100, 'Loading')}", end="", flush=True)
        time.sleep(0.1)
    print()
    
    print("\nSegmented Progress Bar:")
    segmented = ProgressBar(width=50)
    segments = [
        (25, "success"),    # Completed
        (15, "warning"),    # In progress
        (10, "error"),      # Failed
        (50, "info"),       # Remaining
    ]
    
    for i in range(0, 101, 10):
        print(f"\r{segmented.render_segmented(segments, i, 'Tutorial Progress')}", end="", flush=True)
        time.sleep(0.2)
    print()
    
    print("\nSpinners:")
    for style in ["dots", "line", "circle", "bounce", "blocks"]:
        spinner = SpinnerBar(style=style, color="warning")
        print(f"{style:10}", end=" ")
        for _ in range(10):
            print(f"\r{style:10} {spinner.next()}", end="", flush=True)
            time.sleep(0.1)
        print()
    
    print("\nCustom Colors:")
    colors = ["primary", "success", "warning", "error", "learn", "practice"]
    for color in colors:
        bar = ProgressBar(width=25, color_filled=color)
        print(f"{color:10}", bar.render(15, 20))


if __name__ == "__main__":
    demo()