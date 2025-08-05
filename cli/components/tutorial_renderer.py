#!/usr/bin/env python3
"""
Tutorial Renderer - Pure Tutorial Rendering
===========================================
Handles tutorial display without logic concerns.
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.colors import THEME, RESET, BOLD, CLEAR_SCREEN
from cli.components.border import Border, BorderStyle
from cli.components.progress_bar import ProgressBar
from logic.tutorial_engine import TutorialState


class TutorialRenderer:
    """Pure tutorial rendering component."""
    
    def __init__(self, width: Optional[int] = None):
        """Initialize renderer with optional width."""
        # Use a fixed width of 120 for technical content
        self.width = 120
        self.border = Border(
            style=BorderStyle.DOUBLE, 
            color="learn", 
            bold=True,
            show_left=False,
            show_right=False
        )
        self.progress_bar = ProgressBar(
            width=30,
            style="blocks",
            color_filled="success",
            color_empty="text_muted"
        )
        
    def _get_terminal_width(self) -> int:
        """Get terminal width with fallback."""
        try:
            import os
            return min(os.get_terminal_size().columns, 120)  # Increased for technical content
        except:
            return 80
            
    def render_welcome_screen(self, tutorial_data: Dict[str, Any]) -> str:
        """Render welcome screen for tutorial."""
        lines = [CLEAR_SCREEN]
        
        # Simple welcome display
        lines.append(f"\n{THEME['info']}Welcome to: {tutorial_data['title']}{RESET}")
        lines.append(f"{tutorial_data['description']}")
        lines.append(f"\n{THEME['success']}Press Enter to begin...{RESET}")
        
        return "\n".join(lines)
        
    def render_slide_content(
        self, 
        tutorial_data: Dict[str, Any], 
        page_data: Dict[str, Any],
        show_question_prompt: bool = False
    ) -> str:
        """Render slide content in slideshow format."""
        lines = [CLEAR_SCREEN]
        
        # Header
        header_lines = self._render_header(
            tutorial_data['tutorial_id'],
            page_data['title'],
            f"{page_data['slide_number']}/{page_data['total_slides']}",
            tutorial_data.get('completed', False)
        )
        lines.extend(header_lines)
        
        # Content
        content_lines = self._format_content(page_data['content'])
        for line in content_lines:
            lines.append(self.border.middle(self.width, left_text=f"  {line}"))
            
        # Question prompt if needed
        if show_question_prompt and page_data['has_question']:
            lines.append(self.border.empty_line(self.width))
            lines.append(self.border.middle(
                self.width,
                center_text=f"{THEME['warning']}📝 Press Enter for Knowledge Check{RESET}"
            ))
            
        # Add minimal spacing
        lines.append(self.border.empty_line(self.width))
        
        # Footer
        footer_lines = self._render_footer(
            page_data['slide_number'],
            page_data['total_slides'],
            self._get_navigation_hints(show_question_prompt)
        )
        lines.extend(footer_lines)
        
        return "\n".join(lines)
        
    def render_question_screen(
        self,
        tutorial_data: Dict[str, Any],
        page_data: Dict[str, Any],
        question_content: Optional[str] = None
    ) -> str:
        """Render question setup screen with integrated question content."""
        lines = [CLEAR_SCREEN]
        
        # Header
        header_lines = self._render_header(
            tutorial_data['tutorial_id'],
            page_data['title'],
            f"{page_data['slide_number']}/{page_data['total_slides']}",
            tutorial_data.get('completed', False)
        )
        lines.extend(header_lines)
        
        # Question header
        lines.append(self.border.middle(
            self.width,
            left_text=f"  {THEME['warning']}📝 Knowledge Check!{RESET}"
        ))
        lines.append(self.border.empty_line(self.width))
        
        # Question content inside borders
        if question_content:
            # Split question content into lines and add each with border
            content_lines = question_content.split('\n')
            for line in content_lines:
                if line.strip():  # Non-empty lines
                    # Calculate available width for content (accounting for borders and padding)
                    max_content_width = self.width - 6  # 3 chars on each side for border + padding
                    
                    # If line is too long, wrap it
                    if len(self._strip_ansi(line)) > max_content_width:
                        # Simple word wrapping for long lines
                        wrapped_lines = self._wrap_text(line, max_content_width)
                        for wrapped_line in wrapped_lines:
                            lines.append(self.border.middle(self.width, left_text=f"  {wrapped_line}"))
                    else:
                        lines.append(self.border.middle(self.width, left_text=f"  {line}"))
                else:
                    # Empty lines for spacing
                    lines.append(self.border.empty_line(self.width))
        else:
            # Fallback for when no content is provided
            lines.append(self.border.middle(self.width, center_text=""))
        
        lines.append(self.border.empty_line(self.width))
        
        # Footer
        footer_lines = self._render_footer(
            page_data['slide_number'],
            page_data['total_slides'],
            f"{THEME['warning']}Answer the question to continue...{RESET}"
        )
        lines.extend(footer_lines)
        
        return "\n".join(lines)
        
    def render_result_screen(
        self,
        tutorial_data: Dict[str, Any],
        page_data: Dict[str, Any],
        result_data: Dict[str, Any]
    ) -> str:
        """Render question result screen."""
        lines = [CLEAR_SCREEN]
        
        # Header
        header_lines = self._render_header(
            tutorial_data['tutorial_id'],
            page_data['title'],
            f"{page_data['slide_number']}/{page_data['total_slides']}",
            tutorial_data.get('completed', False)
        )
        lines.extend(header_lines)
        
        # Result content
        if result_data['is_correct']:
            lines.append(self.border.middle(
                self.width,
                left_text=f"  {THEME['success']}✅ Correct! Well done!{RESET}"
            ))
        else:
            lines.append(self.border.middle(
                self.width,
                left_text=f"  {THEME['error']}❌ Not quite right.{RESET}"
            ))
            lines.append(self.border.empty_line(self.width))
            lines.append(self.border.middle(
                self.width,
                left_text=f"  The correct answer is: {result_data['correct_option']}"
            ))
            
        # Explanation if available
        if result_data.get('explanation'):
            lines.append(self.border.empty_line(self.width))
            lines.append(self.border.middle(
                self.width,
                left_text=f"  {THEME['info']}📖 Explanation:{RESET}"
            ))
            # Format explanation - wrap long lines
            explanation = result_data['explanation']
            max_width = self.width - 6  # Account for borders and padding
            
            # Simple word wrapping
            words = explanation.split()
            current_line = []
            current_length = 0
            
            for word in words:
                word_length = len(word)
                if current_length + word_length + len(current_line) > max_width:
                    # Wrap to next line
                    if current_line:
                        line_text = " ".join(current_line)
                        lines.append(self.border.middle(self.width, left_text=f"  {line_text}"))
                        current_line = [word]
                        current_length = word_length
                else:
                    current_line.append(word)
                    current_length += word_length
            
            # Add remaining words
            if current_line:
                line_text = " ".join(current_line)
                lines.append(self.border.middle(self.width, left_text=f"  {line_text}"))
                    
        lines.append(self.border.empty_line(self.width))
        
        # Footer
        footer_lines = self._render_footer(
            page_data['slide_number'],
            page_data['total_slides'],
            f"{THEME['info']}Press Enter to continue...{RESET}"
        )
        lines.extend(footer_lines)
        
        return "\n".join(lines)
        
    def render_completion_screen(self, completion_data: Dict[str, Any]) -> str:
        """Render tutorial completion screen."""
        lines = [CLEAR_SCREEN]
        
        # Header
        lines.append(self.border.top(self.width))
        lines.append(self.border.middle(
            self.width,
            left_text=f" TUTORIAL: {completion_data['tutorial_id']}",
            center_text=f"🎉 Tutorial Complete! 🎉",
            right_text="Finished "
        ))
        lines.append(self.border.horizontal_divider(self.width))
        
        # Score
        score_correct, score_total = completion_data['score']
        score_pct = completion_data['score_percentage']
        
        lines.append(self.border.empty_line(self.width))
        lines.append(self.border.middle(
            self.width,
            center_text=f"Score: {score_correct}/{score_total} ({score_pct:.0f}%)"
        ))
        
        # Grade message
        if score_pct >= 80:
            grade_msg = f"{THEME['success']}Excellent work! You've mastered {completion_data['title']}!{RESET}"
        elif score_pct >= 60:
            grade_msg = f"{THEME['warning']}Good job! Consider reviewing the concepts you missed.{RESET}"
        else:
            grade_msg = f"{THEME['warning']}Keep practicing! You might want to review this tutorial again.{RESET}"
            
        lines.append(self.border.middle(self.width, center_text=grade_msg))
        lines.append(self.border.empty_line(self.width))
        
        # Related errors if available
        if completion_data.get('related_errors'):
            lines.append(self.border.middle(
                self.width,
                center_text=f"{THEME['info']}This tutorial helps with these MyPy errors:{RESET}"
            ))
            for error in completion_data['related_errors'][:3]:  # Show top 3
                lines.append(self.border.middle(self.width, center_text=f"  • {error}"))
                
        lines.append(self.border.empty_line(self.width))
        
        # Footer
        lines.append(self.border.horizontal_divider(self.width))
        lines.append(self.border.middle(
            self.width,
            center_text=f"{THEME['info']}Press any key to exit...{RESET}"
        ))
        lines.append(self.border.middle(
            self.width,
            center_text=f"{THEME['info']}Run 'stormcheck tutorial {completion_data['tutorial_id']}' to try again!{RESET}"
        ))
        lines.append(self.border.bottom(self.width))
        
        return "\n".join(lines)
        
    def _render_header(self, tutorial_id: str, title: str, page_info: str, is_completed: bool = False) -> list:
        """Render slideshow header."""
        lines = []
        
        lines.append(self.border.top(self.width))
        
        left = f" TUTORIAL: {tutorial_id}"
        if is_completed:
            left = f" ✅ {left}"
            
        lines.append(self.border.middle(self.width, left_text=left, center_text=title, right_text=f"Page {page_info} "))
        lines.append(self.border.horizontal_divider(self.width))
        
        return lines
        
    def _render_footer(self, current_page: int, total_pages: int, nav_hints: str) -> list:
        """Render slideshow footer."""
        lines = []
        
        lines.append(self.border.horizontal_divider(self.width))
        
        # Progress bar
        progress_text = self.progress_bar.render(current_page, total_pages, label="Progress")
        lines.append(self.border.middle(self.width, center_text=progress_text))
        
        # Navigation hints
        lines.append(self.border.middle(self.width, center_text=nav_hints))
        lines.append(self.border.bottom(self.width))
        
        return lines
        
    def _format_content(self, content: str) -> list:
        """Format content for display."""
        lines = content.split('\n')
        formatted_lines = []
        in_code_block = False
        code_language = None
        code_lines = []
        
        for line in lines:
            # Handle code blocks
            if line.startswith('```'):
                if not in_code_block:
                    # Starting a code block
                    in_code_block = True
                    code_language = line[3:].strip() or 'text'
                    code_lines = []
                else:
                    # Ending a code block
                    in_code_block = False
                    # Format and add the complete code block
                    formatted_code = self._format_code_block(code_lines, code_language)
                    formatted_lines.extend(formatted_code)
                    code_language = None
                    code_lines = []
                continue
                
            # If we're in a code block, collect the lines
            if in_code_block:
                code_lines.append(line)
                continue
                
            # Regular content formatting
            if not line.strip():
                formatted_lines.append("")
                continue
                
            # Process inline markdown formatting before other formatting
            line = self._process_inline_markdown(line)
                
            # Handle headings
            if line.startswith('# '):
                text = line[2:].strip()
                formatted_lines.append(f"{BOLD}{THEME['primary']}{text}{RESET}")
            elif line.startswith('## '):
                text = line[3:].strip()
                formatted_lines.append(f"{BOLD}{THEME['learn']}{text}{RESET}")
            # Handle bullet points
            elif line.startswith('• ') or line.startswith('- '):
                formatted_lines.append(f"{THEME['accent']}• {RESET}{line[2:]}")
            # Handle numbered lists
            elif line[:3].strip() and line[:3].replace('.', '').strip().isdigit():
                parts = line.split('.', 1)
                if len(parts) == 2:
                    num = parts[0].strip()
                    text = parts[1].strip()
                    formatted_lines.append(f"{THEME['accent']}{num}.{RESET} {text}")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
                
        return formatted_lines
        
    def _process_inline_markdown(self, line: str) -> str:
        """Process inline markdown formatting like **bold**, *italic*, and `code`."""
        import re
        
        # Handle bold text: **text** -> bold formatting
        line = re.sub(r'\*\*(.*?)\*\*', f'{BOLD}\\1{RESET}', line)
        
        # Handle italic text: *text* -> underline (since true italics aren't widely supported)
        # Use negative lookahead/lookbehind to avoid matching **bold** patterns
        line = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', f'\033[4m\\1{RESET}', line)
        
        # Handle inline code: `text` -> code styling
        line = re.sub(r'`([^`]+?)`', f'{THEME["info"]}\\1{RESET}', line)
        
        return line
        
    def _format_code_block(self, code_lines: List[str], language: str) -> List[str]:
        """Format a code block with syntax highlighting."""
        formatted_lines = []
        
        # Try to use Rich for syntax highlighting
        try:
            from rich.syntax import Syntax
            from rich.console import Console
            
            # Join code lines
            code = '\n'.join(code_lines)
            
            # Create a syntax object
            syntax = Syntax(
                code,
                language,
                theme="monokai",
                line_numbers=False,
                code_width=self.width - 10  # Account for borders and padding
            )
            
            # Render to string
            console = Console(width=self.width - 6, legacy_windows=False)
            with console.capture() as capture:
                console.print(syntax, highlight=True)
            
            # Split rendered output into lines
            rendered = capture.get()
            for line in rendered.strip().split('\n'):
                # Strip ANSI codes to check line length
                stripped = self._strip_ansi(line)
                if len(stripped) <= self.width - 6:
                    formatted_lines.append(line)
                else:
                    # Line too long, use fallback
                    formatted_lines.append(line[:self.width - 9] + "...")
                    
        except ImportError:
            # Fallback without Rich - use simple coloring
            formatted_lines.extend(self._format_code_block_fallback(code_lines, language))
            
        return formatted_lines
        
    def _format_code_block_fallback(self, code_lines: List[str], language: str) -> List[str]:
        """Fallback code formatting without Rich."""
        formatted_lines = []
        
        # Add language indicator
        formatted_lines.append(f"{THEME['text_muted']}[{language}]{RESET}")
        
        # Format each line with basic syntax coloring
        for line in code_lines:
            if language in ['python', 'py']:
                # Basic Python syntax coloring
                formatted_line = line
                # Color strings
                formatted_line = re.sub(r'(["\'])([^"\']*)\1', f"{THEME['success']}\\1\\2\\1{RESET}", formatted_line)
                # Color comments
                formatted_line = re.sub(r'(#.*)', f"{THEME['text_muted']}\\1{RESET}", formatted_line)
                # Color keywords
                keywords = ['def', 'class', 'import', 'from', 'return', 'if', 'else', 'for', 'while', 'True', 'False', 'None']
                for kw in keywords:
                    formatted_line = re.sub(rf'\b({kw})\b', f"{THEME['accent']}\\1{RESET}", formatted_line)
                formatted_lines.append(f"{THEME['info']}{formatted_line}{RESET}")
            elif language in ['toml', 'ini']:
                # Basic TOML syntax coloring
                formatted_line = line
                # Color section headers
                formatted_line = re.sub(r'(\[.*\])', f"{THEME['primary']}\\1{RESET}", formatted_line)
                # Color keys
                formatted_line = re.sub(r'^(\s*)(\w+)(\s*=)', f"\\1{THEME['learn']}\\2{RESET}\\3", formatted_line)
                # Color strings
                formatted_line = re.sub(r'(["\'])([^"\']*)\1', f"{THEME['success']}\\1\\2\\1{RESET}", formatted_line)
                # Color booleans
                formatted_line = re.sub(r'\b(true|false)\b', f"{THEME['accent']}\\1{RESET}", formatted_line)
                formatted_lines.append(formatted_line)
            else:
                # Default formatting
                formatted_lines.append(f"{THEME['info']}{line}{RESET}")
                
        return formatted_lines
        
    def _get_navigation_hints(self, has_question: bool) -> str:
        """Get navigation hints based on context."""
        if has_question:
            return f"{THEME['warning']}[Enter: Knowledge Check | b: Back | q: Quit]{RESET}"
        else:
            return f"{THEME['info']}[Enter: Next | b: Back | q: Quit]{RESET}"
    
    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max_width, preserving ANSI codes."""
        # For now, simple word-based wrapping
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(self._strip_ansi(word))
            if current_length + word_length + len(current_line) > max_width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    # Word is too long, force break
                    lines.append(word)
                    current_line = []
                    current_length = 0
            else:
                current_line.append(word)
                current_length += word_length
        
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines