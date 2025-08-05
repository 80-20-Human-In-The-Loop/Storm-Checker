#!/usr/bin/env python3
"""
Beautiful Border Drawing Component for Storm-Checker
====================================================
Create stunning borders and boxes for CLI interfaces using Storm-Checker colors.
"""

import os
from enum import Enum
from typing import List, Optional, Tuple

# Import our color system
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from storm_checker.cli.colors import THEME, RESET, BOLD


class BorderStyle(Enum):
    """Available border styles."""
    SINGLE = {
        'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
        'h': '─', 'v': '│', 't_down': '┬', 't_up': '┴',
        't_right': '├', 't_left': '┤', 'cross': '┼'
    }
    DOUBLE = {
        'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝',
        'h': '═', 'v': '║', 't_down': '╦', 't_up': '╩',
        't_right': '╠', 't_left': '╣', 'cross': '╬'
    }
    ROUNDED = {
        'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯',
        'h': '─', 'v': '│', 't_down': '┬', 't_up': '┴',
        't_right': '├', 't_left': '┤', 'cross': '┼'
    }
    HEAVY = {
        'tl': '┏', 'tr': '┓', 'bl': '┗', 'br': '┛',
        'h': '━', 'v': '┃', 't_down': '┳', 't_up': '┻',
        't_right': '┣', 't_left': '┫', 'cross': '╋'
    }
    ASCII = {
        'tl': '+', 'tr': '+', 'bl': '+', 'br': '+',
        'h': '-', 'v': '|', 't_down': '+', 't_up': '+',
        't_right': '+', 't_left': '+', 'cross': '+'
    }


class Border:
    """Create beautiful borders for CLI components."""
    
    def __init__(
        self,
        style: BorderStyle = BorderStyle.SINGLE,
        color: Optional[str] = None,
        bold: bool = False,
        show_left: bool = True,
        show_right: bool = False
    ):
        """
        Initialize border with style and color.
        
        Args:
            style: Border style to use
            color: Color name from THEME or None for default
            bold: Whether to make border bold
            show_left: Whether to show left border (default True)
            show_right: Whether to show right border (default False for better alignment)
        """
        self.style = style
        self.chars = style.value
        self.color = THEME.get(color, "") if color else THEME["primary"]
        self.bold_style = BOLD if bold else ""
        self.show_left = show_left
        self.show_right = show_right
        
    def _colored(self, text: str) -> str:
        """Apply color and style to text."""
        return f"{self.bold_style}{self.color}{text}{RESET}"
        
    def top(self, width: int) -> str:
        """Draw top border line."""
        if self.show_left and self.show_right:
            return self._colored(
                self.chars['tl'] + self.chars['h'] * (width - 2) + self.chars['tr']
            )
        elif self.show_left:
            return self._colored(
                self.chars['tl'] + self.chars['h'] * (width - 1)
            )
        elif self.show_right:
            return self._colored(
                self.chars['h'] * (width - 1) + self.chars['tr']
            )
        else:
            return self._colored(self.chars['h'] * width)
        
    def bottom(self, width: int) -> str:
        """Draw bottom border line."""
        if self.show_left and self.show_right:
            return self._colored(
                self.chars['bl'] + self.chars['h'] * (width - 2) + self.chars['br']
            )
        elif self.show_left:
            return self._colored(
                self.chars['bl'] + self.chars['h'] * (width - 1)
            )
        elif self.show_right:
            return self._colored(
                self.chars['h'] * (width - 1) + self.chars['br']
            )
        else:
            return self._colored(self.chars['h'] * width)
        
    def middle(self, width: int, left_text: str = "", center_text: str = "", right_text: str = "") -> str:
        """
        Draw middle border line with optional text sections.
        
        Args:
            width: Total width of the border
            left_text: Text for left section
            center_text: Text for center section
            right_text: Text for right section
        """
        # Calculate available space
        border_chars = (1 if self.show_left else 0) + (1 if self.show_right else 0)
        available = width - border_chars
        
        # Remove ANSI codes for length calculation
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        left_len = len(ansi_escape.sub('', left_text))
        center_len = len(ansi_escape.sub('', center_text))
        right_len = len(ansi_escape.sub('', right_text))
        
        # Calculate padding
        total_text_len = left_len + center_len + right_len
        
        if total_text_len > available:
            # Truncate if too long
            max_section = available // 3
            if left_len > max_section:
                left_text = left_text[:max_section-3] + "..."
                left_len = max_section
            if center_len > max_section:
                center_text = center_text[:max_section-3] + "..."
                center_len = max_section
            if right_len > max_section:
                right_text = right_text[:max_section-3] + "..."
                right_len = max_section
        
        # Calculate spacing
        if center_text:
            # Distribute space around center
            left_pad = (available - center_len) // 2 - left_len
            right_pad = available - left_len - center_len - left_pad
            
            line = (
                (self._colored(self.chars['v']) if self.show_left else "") +
                (" " * 1 if left_text and self.show_left else "") + left_text +
                " " * (left_pad - (1 if left_text and self.show_left else 0)) +
                center_text +
                " " * (right_pad - right_len - (1 if right_text and self.show_right else 0)) +
                right_text + (" " * 1 if right_text and self.show_right else "") +
                (self._colored(self.chars['v']) if self.show_right else "")
            )
        else:
            # Just left and right
            left_padding = 1 if self.show_left else 0
            right_padding = 1 if self.show_right else 0
            middle_space = available - left_len - right_len - (left_padding if left_text else 0) - (right_padding if right_text else 0)
            line = (
                (self._colored(self.chars['v']) if self.show_left else "") +
                (" " * 1 if left_text and self.show_left else "") + left_text +
                " " * middle_space +
                right_text + (" " * 1 if right_text and self.show_right else "") +
                (self._colored(self.chars['v']) if self.show_right else "")
            )
            
        return line
        
    def empty_line(self, width: int) -> str:
        """Draw an empty bordered line."""
        if self.show_left and self.show_right:
            return self._colored(self.chars['v']) + " " * (width - 2) + self._colored(self.chars['v'])
        elif self.show_left:
            return self._colored(self.chars['v']) + " " * (width - 1)
        elif self.show_right:
            return " " * (width - 1) + self._colored(self.chars['v'])
        else:
            return " " * width
        
    def horizontal_divider(self, width: int) -> str:
        """Draw a horizontal divider within the border."""
        if self.show_left and self.show_right:
            return self._colored(
                self.chars['t_right'] + self.chars['h'] * (width - 2) + self.chars['t_left']
            )
        elif self.show_left:
            return self._colored(
                self.chars['t_right'] + self.chars['h'] * (width - 1)
            )
        elif self.show_right:
            return self._colored(
                self.chars['h'] * (width - 1) + self.chars['t_left']
            )
        else:
            return self._colored(self.chars['h'] * width)
        
    def box(
        self,
        content: List[str],
        width: Optional[int] = None,
        padding: int = 1,
        align: str = "left"
    ) -> List[str]:
        """
        Create a complete box around content.
        
        Args:
            content: List of content lines
            width: Box width (auto-detected if None)
            padding: Internal padding
            align: Text alignment (left, center, right)
            
        Returns:
            List of lines forming the complete box
        """
        if width is None:
            # Auto-detect width based on content
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            max_len = max(len(ansi_escape.sub('', line)) for line in content) if content else 0
            width = max_len + (padding * 2) + 2  # +2 for borders
            
        # Ensure minimum width
        width = max(width, 10)
        
        lines = []
        
        # Top border
        lines.append(self.top(width))
        
        # Top padding
        for _ in range(padding):
            lines.append(self.empty_line(width))
            
        # Content lines
        for line in content:
            # Remove ANSI for alignment calculation
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_line = ansi_escape.sub('', line)
            line_len = len(clean_line)
            
            available = width - 2 - (padding * 2)
            
            if align == "center":
                left_space = (available - line_len) // 2
                right_space = available - line_len - left_space
                formatted = " " * (padding + left_space) + line + " " * (padding + right_space)
            elif align == "right":
                formatted = " " * (available - line_len + padding) + line + " " * padding
            else:  # left
                formatted = " " * padding + line + " " * (available - line_len + padding)
                
            left_border = self._colored(self.chars['v']) if self.show_left else ""
            right_border = self._colored(self.chars['v']) if self.show_right else ""
            lines.append(left_border + formatted + right_border)
            
        # Bottom padding
        for _ in range(padding):
            lines.append(self.empty_line(width))
            
        # Bottom border
        lines.append(self.bottom(width))
        
        return lines


def get_terminal_width() -> int:
    """Get terminal width, with fallback."""
    try:
        return os.get_terminal_size().columns
    except:
        return 80  # Default fallback


def demo():
    """Demo various border styles and features."""
    print("\n=== Storm-Checker Border Component Demo ===\n")
    
    # Demo different styles
    styles = [
        (BorderStyle.SINGLE, "primary", "Single Style"),
        (BorderStyle.DOUBLE, "success", "Double Style"),
        (BorderStyle.ROUNDED, "warning", "Rounded Style"),
        (BorderStyle.HEAVY, "error", "Heavy Style"),
    ]
    
    for style, color, name in styles:
        border = Border(style=style, color=color, bold=True)
        
        # Simple box
        box_lines = border.box([name], width=30, align="center")
        for line in box_lines:
            print(line)
        print()
    
    # Demo header layout
    print("Header Layout Demo:")
    border = Border(style=BorderStyle.DOUBLE, color="learn", bold=True)
    
    print(border.top(80))
    print(border.middle(80, "TUTORIAL: hello_world", "Introduction to Type Hints", "1/4"))
    print(border.horizontal_divider(80))
    print(border.empty_line(80))
    
    # Content
    content = [
        "Welcome to the Storm-Checker tutorial system!",
        "",
        "This tutorial will teach you the basics of Python type hints.",
        "You'll learn how to make your code more maintainable and catch bugs early."
    ]
    
    for line in content:
        print(border.middle(80, center_text=line))
        
    print(border.empty_line(80))
    print(border.bottom(80))


if __name__ == "__main__":
    demo()