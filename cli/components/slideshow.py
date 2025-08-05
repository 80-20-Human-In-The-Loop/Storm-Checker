#!/usr/bin/env python3
"""
Slideshow Component for Storm-Checker Tutorials
===============================================
Beautiful slideshow renderer with header layout and navigation.
"""

import os
import sys
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

# Import our components
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from cli.colors import THEME, PALETTE, RESET, BOLD, CLEAR_SCREEN, CURSOR_HIDE, CURSOR_SHOW
from cli.components.border import Border, BorderStyle
from cli.components.progress_bar import ProgressBar


class ContentMode(Enum):
    """Content display modes for tutorial slideshow."""
    SLIDE = "slide"           # Show slide content
    QUESTION = "question"     # Show question within slideshow  
    RESULT = "result"         # Show question result


@dataclass
class Slide:
    """Represents a single slide in the slideshow."""
    title: str
    content: str
    slide_number: int
    total_slides: int
    tutorial_id: Optional[str] = None
    has_question: bool = False


class Slideshow:
    """Beautiful slideshow renderer for tutorials."""
    
    def __init__(
        self,
        border_style: BorderStyle = BorderStyle.DOUBLE,
        border_color: str = "learn",
        width: Optional[int] = None,
        height: Optional[int] = None
    ):
        """
        Initialize slideshow.
        
        Args:
            border_style: Border style to use
            border_color: Color for borders
            width: Terminal width (auto-detected if None)
            height: Terminal height (auto-detected if None)
        """
        self.border = Border(style=border_style, color=border_color, bold=True)
        self.width = width or self._get_terminal_width()
        self.height = height or self._get_terminal_height()
        self.progress_bar = ProgressBar(
            width=30,
            style="blocks",
            color_filled="success",
            color_empty="text_muted"
        )
        
    def _get_terminal_width(self) -> int:
        """Get terminal width with fallback."""
        try:
            return min(os.get_terminal_size().columns, 120)  # Increased for technical content
        except:
            return 80
            
    def _get_terminal_height(self) -> int:
        """Get terminal height with fallback."""
        try:
            return os.get_terminal_size().lines
        except:
            return 24
            
    def render_header(
        self,
        tutorial_id: str,
        slide_title: str,
        page_info: str,
        is_completed: bool = False
    ) -> List[str]:
        """
        Render the slideshow header.
        
        Args:
            tutorial_id: Tutorial identifier (e.g., "pyproject_setup")
            slide_title: Title of current slide
            page_info: Page indicator (e.g., "2/5")
            is_completed: Whether this tutorial is completed
            
        Returns:
            List of header lines
        """
        lines = []
        
        # Top border
        lines.append(self.border.top(self.width))
        
        # Header content with three sections
        left = f" TUTORIAL: {tutorial_id}"
        if is_completed:
            left = f" ✅ {left}"
            
        center = slide_title
        right = f"Page {page_info} "
        
        lines.append(self.border.middle(self.width, left, center, right))
        
        # Divider
        lines.append(self.border.horizontal_divider(self.width))
        
        return lines
        
    def render_footer(
        self,
        navigation_hints: Optional[str] = None,
        progress: Optional[Tuple[int, int]] = None
    ) -> List[str]:
        """
        Render the slideshow footer.
        
        Args:
            navigation_hints: Navigation instructions
            progress: (current, total) for progress bar
            
        Returns:
            List of footer lines
        """
        lines = []
        
        # Divider
        lines.append(self.border.horizontal_divider(self.width))
        
        # Progress bar
        if progress:
            current, total = progress
            progress_text = self.progress_bar.render(
                current, total,
                label="Progress"
            )
            # Center the progress bar
            padding = (self.width - len(self._strip_ansi(progress_text)) - 2) // 2
            lines.append(
                self.border.middle(self.width, center_text=" " * padding + progress_text)
            )
        
        # Navigation hints
        if navigation_hints:
            lines.append(
                self.border.middle(self.width, center_text=navigation_hints)
            )
        
        # Bottom border
        lines.append(self.border.bottom(self.width))
        
        return lines
        
    def render_slide(
        self,
        slide: Slide,
        is_completed: bool = False,
        navigation_hints: Optional[str] = None
    ) -> str:
        """
        Render a complete slide.
        
        Args:
            slide: Slide to render
            is_completed: Whether the tutorial is completed
            navigation_hints: Navigation instructions
            
        Returns:
            Complete rendered slide as string
        """
        lines = []
        
        # Clear screen
        lines.append(CLEAR_SCREEN)
        
        # Header
        page_info = f"{slide.slide_number}/{slide.total_slides}"
        header_lines = self.render_header(
            slide.tutorial_id or "tutorial",
            slide.title,
            page_info,
            is_completed
        )
        lines.extend(header_lines)
        
        # Render content (dynamic height, no artificial padding)
        content_lines = self._format_content(slide.content, max_lines=100)  # Increased for comprehensive content
        for line in content_lines:
            lines.append(self.border.middle(self.width, left_text=f"  {line}"))
        
        # Add minimal spacing for readability
        lines.append(self.border.empty_line(self.width))
            
        # Footer
        progress = (slide.slide_number, slide.total_slides)
        footer_lines = self.render_footer(navigation_hints, progress)
        lines.extend(footer_lines)
        
        return "\n".join(lines)
        
    def render_dynamic_content(
        self,
        slide: Slide,
        mode: ContentMode,
        content_data: Optional[str] = None,
        is_completed: bool = False,
        navigation_hints: Optional[str] = None
    ) -> str:
        """
        Render slideshow with dynamic content modes.
        
        Args:
            slide: Slide information (for header/footer)
            mode: Content display mode
            content_data: Additional content for question/result modes
            is_completed: Whether the tutorial is completed
            navigation_hints: Navigation instructions
            
        Returns:
            Complete rendered slideshow as string
        """
        lines = []
        
        # Clear screen
        lines.append(CLEAR_SCREEN)
        
        # Header (always same)
        page_info = f"{slide.slide_number}/{slide.total_slides}"
        header_lines = self.render_header(
            slide.tutorial_id or "tutorial",
            slide.title,
            page_info,
            is_completed
        )
        lines.extend(header_lines)
        
        # Dynamic content area based on mode
        if mode == ContentMode.SLIDE:
            # Show slide content + question prompt if needed
            content_lines = self._format_content(slide.content, max_lines=80)
            for line in content_lines:
                lines.append(self.border.middle(self.width, left_text=f"  {line}"))
                
            # Add question prompt if this slide has a question
            if slide.has_question:
                lines.append(self.border.empty_line(self.width))
                lines.append(self.border.middle(
                    self.width, 
                    center_text=f"{THEME['warning']}📝 Press Enter for Knowledge Check{RESET}"
                ))
                
        elif mode == ContentMode.QUESTION:
            # Show question header and prepare space for question content
            lines.append(self.border.middle(
                self.width, 
                center_text=f"{THEME['warning']}📝 Knowledge Check!{RESET}"
            ))
            lines.append(self.border.empty_line(self.width))
            
            # Space for question content (will be rendered by MultipleChoice)
            # This creates a clean area within the slideshow border
            if content_data:
                question_lines = content_data.split('\n')
                for line in question_lines:
                    lines.append(self.border.middle(self.width, center_text=line))
            
        elif mode == ContentMode.RESULT:
            # Show question result
            lines.append(self.border.middle(
                self.width, 
                center_text=f"{THEME['info']}📊 Question Result{RESET}"
            ))
            lines.append(self.border.empty_line(self.width))
            
            if content_data:
                result_lines = content_data.split('\n')
                for line in result_lines:
                    lines.append(self.border.middle(self.width, center_text=line))
        
        # Add minimal spacing
        lines.append(self.border.empty_line(self.width))
        
        # Footer with progress (always same)
        progress = (slide.slide_number, slide.total_slides)
        footer_lines = self.render_footer(navigation_hints, progress)
        lines.extend(footer_lines)
        
        return "\n".join(lines)
        
    def _format_content(self, content: str, max_lines: int) -> List[str]:
        """
        Format content to fit within the slide.
        
        Args:
            content: Raw content text
            max_lines: Maximum number of lines
            
        Returns:
            List of formatted content lines
        """
        lines = content.split("\n")
        formatted_lines = []
        
        # Process each line
        for line in lines:
            if not line.strip():
                formatted_lines.append("")
                continue
                
            # Handle code blocks
            if line.startswith("```"):
                formatted_lines.append(self._format_code_delimiter(line))
                continue
                
            # Handle headings
            if line.startswith("#"):
                formatted_lines.append(self._format_heading(line))
                continue
                
            # Handle bullet points
            if line.startswith("- ") or line.startswith("• "):
                formatted_lines.append(self._format_bullet(line))
                continue
                
            # Handle numbered lists
            if line[:3].strip() and line[:3].replace(".", "").strip().isdigit():
                formatted_lines.append(self._format_numbered(line))
                continue
                
            # Regular text - wrap if needed
            wrapped = self._wrap_text(line, self.width - 6)  # Account for borders and padding
            formatted_lines.extend(wrapped)
            
        # Truncate if too long
        if len(formatted_lines) > max_lines:
            formatted_lines = formatted_lines[:max_lines-1]
            formatted_lines.append(f"{THEME['warning']}... (content truncated){RESET}")
            
        return formatted_lines
        
    def _format_heading(self, line: str) -> str:
        """Format heading with colors."""
        level = len(line) - len(line.lstrip("#"))
        text = line.lstrip("#").strip()
        
        if level == 1:
            return f"{BOLD}{THEME['primary']}{text}{RESET}"
        elif level == 2:
            return f"{BOLD}{THEME['learn']}{text}{RESET}"
        else:
            return f"{THEME['info']}{text}{RESET}"
            
    def _format_bullet(self, line: str) -> str:
        """Format bullet point."""
        return f"{THEME['accent']}• {RESET}{line[2:]}"
        
    def _format_numbered(self, line: str) -> str:
        """Format numbered list item."""
        parts = line.split(".", 1)
        if len(parts) == 2:
            num = parts[0].strip()
            text = parts[1].strip()
            return f"{THEME['accent']}{num}.{RESET} {text}"
        return line
        
    def _format_code_delimiter(self, line: str) -> str:
        """Format code block delimiter."""
        return f"{THEME['text_muted']}{line}{RESET}"
        
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        if len(text) <= max_width:
            return [text]
            
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            if current_length + word_length + len(current_line) > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    # Word is too long, split it
                    lines.append(word[:max_width])
                    current_line = [word[max_width:]]
                    current_length = len(word[max_width:])
            else:
                current_line.append(word)
                current_length += word_length
                
        if current_line:
            lines.append(" ".join(current_line))
            
        return lines
        
    def _strip_ansi(self, text: str) -> str:
        """Strip ANSI codes from text."""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
        
    def render_completion_screen(
        self,
        tutorial_id: str,
        score: Tuple[int, int],
        message: str,
        achievements: Optional[List[str]] = None
    ) -> str:
        """
        Render tutorial completion screen.
        
        Args:
            tutorial_id: Tutorial identifier
            score: (correct, total) questions
            message: Completion message
            achievements: List of achievements earned
            
        Returns:
            Rendered completion screen
        """
        lines = []
        
        # Clear screen
        lines.append(CLEAR_SCREEN)
        
        # Special completion header
        lines.append(self.border.top(self.width))
        # Show "Finished" instead of page numbers
        left = f" TUTORIAL: {tutorial_id}"
        center = f"🎉 Tutorial Complete! 🎉"
        right = "Finished "
        lines.append(
            self.border.middle(
                self.width, 
                left=f"{THEME['success']}{left}{RESET}",
                center=f"{BOLD}{THEME['success']}{center}{RESET}",
                right=f"{THEME['success']}{right}{RESET}"
            )
        )
        lines.append(self.border.horizontal_divider(self.width))
        
        # Score
        correct, total = score
        percentage = (correct / total * 100) if total > 0 else 0
        score_text = f"Score: {correct}/{total} ({percentage:.0f}%)"
        
        if percentage >= 80:
            score_color = "success"
            grade = "Excellent!"
        elif percentage >= 60:
            score_color = "warning"
            grade = "Good job!"
        else:
            score_color = "error"
            grade = "Keep practicing!"
            
        lines.append(self.border.empty_line(self.width))
        lines.append(
            self.border.middle(
                self.width,
                center_text=f"{THEME[score_color]}{score_text} - {grade}{RESET}"
            )
        )
        lines.append(self.border.empty_line(self.width))
        
        # Message
        for line in message.split("\n"):
            lines.append(self.border.middle(self.width, center_text=line))
            
        # Achievements
        if achievements:
            lines.append(self.border.empty_line(self.width))
            lines.append(self.border.horizontal_divider(self.width))
            lines.append(
                self.border.middle(
                    self.width,
                    center_text=f"{THEME['accent']}🏆 Achievements Earned:{RESET}"
                )
            )
            for achievement in achievements:
                lines.append(
                    self.border.middle(self.width, center_text=f"  {achievement}")
                )
                
        # Fill remaining space
        lines_used = len(lines)
        remaining = self.height - lines_used - 1
        for _ in range(max(0, remaining - 3)):
            lines.append(self.border.empty_line(self.width))
            
        # Footer
        lines.append(self.border.horizontal_divider(self.width))
        lines.append(
            self.border.middle(
                self.width,
                center_text=f"{THEME['info']}Press any key to exit...{RESET}"
            )
        )
        lines.append(self.border.bottom(self.width))
        
        return "\n".join(lines)


def demo():
    """Demo the slideshow component."""
    import time
    
    slideshow = Slideshow()
    
    # Demo slides
    slides = [
        Slide(
            title="Introduction to Type Hints",
            content="""# Welcome to Type Hints!

Python type hints help you write better, more maintainable code.

## Benefits:
- Catch bugs before runtime
- Better IDE support
- Self-documenting code
- Easier refactoring

Let's learn how to use them effectively!""",
            slide_number=1,
            total_slides=3,
            tutorial_id="type_hints_basics"
        ),
        Slide(
            title="Basic Syntax",
            content="""# Type Hint Syntax

Here's how to add type hints to your code:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

age: int = 25
prices: list[float] = [9.99, 19.99, 29.99]
```

## Key Points:
1. Use `:` after parameter names
2. Use `->` for return types
3. Variables can also have type hints""",
            slide_number=2,
            total_slides=3,
            tutorial_id="type_hints_basics",
            has_question=True
        ),
        Slide(
            title="Advanced Types",
            content="""# Advanced Type Hints

Python's typing module provides advanced types:

• Optional[T] - Value can be T or None
• Union[A, B] - Value can be A or B
• List[T] - List of type T
• Dict[K, V] - Dictionary with key type K, value type V
• Callable[[Args], Return] - Function types

Remember: Type hints are optional but highly recommended!""",
            slide_number=3,
            total_slides=3,
            tutorial_id="type_hints_basics"
        ),
    ]
    
    # Show slides
    for i, slide in enumerate(slides):
        is_completed = i == 0  # Demo completed state on first slide
        nav_hints = f"{THEME['info']}[Enter: Next | b: Back | q: Quit]{RESET}"
        
        if slide.has_question:
            nav_hints = f"{THEME['warning']}⚠️  Question ahead! {nav_hints}{RESET}"
            
        print(slideshow.render_slide(slide, is_completed, nav_hints))
        
        if i < len(slides) - 1:
            input("\nPress Enter for next slide...")
            
    # Show completion screen
    print(slideshow.render_completion_screen(
        "type_hints_basics",
        (2, 2),
        "Congratulations! You've mastered the basics of type hints.\n\nYou're ready to write more maintainable Python code!",
        ["🎯 First Steps", "📚 Quick Learner"]
    ))


if __name__ == "__main__":
    print(CURSOR_HIDE, end="")
    try:
        demo()
    finally:
        print(CURSOR_SHOW, end="")