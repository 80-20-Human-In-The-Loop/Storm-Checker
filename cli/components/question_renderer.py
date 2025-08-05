#!/usr/bin/env python3
"""
Question Renderer - Pure Question Rendering
===========================================
Formats question data for display without handling interaction.
"""

import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.colors import THEME, RESET, BOLD


class QuestionRenderer:
    """Pure question rendering component."""
    
    def format_question_text(self, question_data: Dict) -> str:
        """Format question text with styling."""
        return f"{THEME['learn']}{BOLD}📚 {question_data['question_text']}{RESET}"
        
    def format_hint(self, question_data: Dict) -> str:
        """Format hint text if available."""
        if question_data.get('hint') and not question_data['is_answered']:
            return f"{THEME['warning']}💡 Hint: {question_data['hint']}{RESET}"
        return ""
        
    def format_options(self, question_data: Dict) -> List[str]:
        """Format question options for display."""
        formatted_options = []
        
        for i, option in enumerate(question_data['options']):
            is_selected = i == question_data['selected_index']
            prefix = "▶ " if is_selected else "  "
            number = f"{i + 1}."
            
            if question_data['is_answered']:
                # Show correct/incorrect after answering
                if i == question_data['correct_index']:
                    color = THEME['success']
                    symbol = " ✓"
                elif i == question_data.get('user_answer') and i != question_data['correct_index']:
                    color = THEME['error']  
                    symbol = " ✗"
                else:
                    color = ""
                    symbol = ""
                formatted_options.append(f"{color}{prefix}{number} {option}{symbol}{RESET}")
            else:
                # Show selection during navigation
                if is_selected:
                    formatted_options.append(f"{THEME['info']}{BOLD}{prefix}{number} {option}{RESET}")
                else:
                    formatted_options.append(f"  {number} {option}")
                    
        return formatted_options
        
    def format_complete_question(self, question_data: Dict) -> str:
        """Format complete question display."""
        lines = []
        
        # Question text
        question_text = self.format_question_text(question_data)
        lines.append(question_text)
        
        # Hint if available
        hint_text = self.format_hint(question_data)
        if hint_text:
            lines.append(hint_text)
            
        # Empty line for spacing
        lines.append("")
        
        # Options
        options = self.format_options(question_data)
        lines.extend(options)
        
        return "\n".join(lines)
        
    def format_navigation_help(self) -> str:
        """Format navigation help text."""
        return f"{THEME['text_muted']}Use ↑↓ or 1-9 to select, Enter to confirm{RESET}"