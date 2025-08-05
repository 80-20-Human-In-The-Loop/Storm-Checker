#!/usr/bin/env python3
"""
Interactive Multiple Choice Component for Storm-Checker Tutorials
=================================================================
A beautiful, keyboard-navigable multiple choice interface for educational content.
"""

import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple
import termios
import tty

# Color constants for educational theme
LEARN_BLUE = "\033[94m"
LEARN_GREEN = "\033[92m"
LEARN_YELLOW = "\033[93m"
LEARN_PURPLE = "\033[95m"
LEARN_CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR_LINE = "\033[K"
CURSOR_UP = "\033[A"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


@dataclass
class Question:
    """Represents a multiple choice question."""
    text: str
    options: List[str]
    correct_index: int
    explanation: Optional[str] = None
    hint: Optional[str] = None


class MultipleChoice:
    """
    Interactive multiple choice component with keyboard navigation.
    
    Features:
    - Arrow key navigation
    - Number key shortcuts (1-9)
    - Visual feedback with colors and symbols
    - Explanations after answer selection
    """
    
    def __init__(self, question: Question, integrated_mode: bool = False):
        self.question = question
        self.selected_index = 0
        self.answered = False
        self.user_answer: Optional[int] = None
        self.integrated_mode = integrated_mode  # Don't clear screen if in slideshow
        
    def display(self, clear_previous: bool = False) -> None:
        """Display the question and options with current selection highlighted."""
        if clear_previous and not self.integrated_mode:
            # Simple clear screen approach instead of complex line counting
            print("\033[2J\033[H", end="")  # Clear screen and move to top
                
        # Display question
        print(f"\n{LEARN_BLUE}{BOLD}📚 {self.question.text}{RESET}")
        
        # Display hint if available and not answered
        if self.question.hint and not self.answered:
            print(f"{LEARN_YELLOW}💡 Hint: {self.question.hint}{RESET}")
        
        print()  # Empty line for spacing
        
        # Display options
        for i, option in enumerate(self.question.options):
            is_selected = i == self.selected_index
            prefix = "▶ " if is_selected else "  "
            number = f"{i + 1}."
            
            if self.answered:
                # Show correct/incorrect after answering
                if i == self.question.correct_index:
                    color = LEARN_GREEN
                    symbol = "✓"
                elif i == self.user_answer and i != self.question.correct_index:
                    color = "\033[91m"  # Red
                    symbol = "✗"
                else:
                    color = ""
                    symbol = " "
                print(f"{color}{prefix}{number} {option} {symbol}{RESET}")
            else:
                # Show selection during navigation
                if is_selected:
                    print(f"{LEARN_CYAN}{BOLD}{prefix}{number} {option}{RESET}")
                else:
                    print(f"  {number} {option}")
                    
    def get_key(self) -> str:
        """Get a single keypress from the user."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
            
            # Handle special keys (arrow keys send escape sequences)
            if key == '\x1b':  # ESC sequence
                key += sys.stdin.read(2)
                if key == '\x1b[A':  # Up arrow
                    return 'UP'
                elif key == '\x1b[B':  # Down arrow
                    return 'DOWN'
            elif key in '123456789' and int(key) <= len(self.question.options):
                return key
            elif key == '\r' or key == '\n':  # Enter
                return 'ENTER'
            elif key == 'q' or key == '\x03':  # q or Ctrl+C
                return 'QUIT'
                
            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    def run(self) -> Tuple[bool, int]:
        """
        Run the interactive multiple choice question.
        
        Returns:
            Tuple of (is_correct, selected_index)
        """
        print(HIDE_CURSOR, end="", flush=True)  # Hide cursor for cleaner display
        
        try:
            self.display()
            
            while not self.answered:
                key = self.get_key()
                
                if key == 'UP' and self.selected_index > 0:
                    self.selected_index -= 1
                    self.display(clear_previous=True)
                elif key == 'DOWN' and self.selected_index < len(self.question.options) - 1:
                    self.selected_index += 1
                    self.display(clear_previous=True)
                elif key in '123456789':
                    # Direct number selection
                    index = int(key) - 1
                    if 0 <= index < len(self.question.options):
                        self.selected_index = index
                        self.answer_question()
                elif key == 'ENTER':
                    self.answer_question()
                    break  # Exit the loop after answering
                elif key == 'QUIT':
                    print(SHOW_CURSOR, end="", flush=True)
                    print(f"\n{LEARN_YELLOW}Exiting tutorial...{RESET}")
                    sys.exit(0)
                    
            return (self.user_answer == self.question.correct_index, self.user_answer)
            
        finally:
            print(SHOW_CURSOR, end="", flush=True)  # Always show cursor again
            
    def answer_question(self) -> None:
        """Process the answer and show result."""
        self.answered = True
        self.user_answer = self.selected_index
        self.display(clear_previous=True)
        
        # Show result message
        print()
        if self.user_answer == self.question.correct_index:
            print(f"{LEARN_GREEN}{BOLD}✅ Correct! Well done!{RESET}")
        else:
            print(f"\033[91m{BOLD}❌ Not quite right.{RESET}")
            print(f"{LEARN_YELLOW}The correct answer is: {self.question.options[self.question.correct_index]}{RESET}")
            
        # Show explanation if provided
        if self.question.explanation:
            print(f"\n{LEARN_PURPLE}📖 Explanation:{RESET}")
            print(f"{self.question.explanation}")
            
        # Don't wait for key here - let the tutorial handle navigation
        print()  # Just add spacing


# TODO: Add timer feature for quiz mode
# TODO: Add support for multi-select questions
# TODO: Add keyboard shortcut help display
# TODO: Add accessibility mode with screen reader support


def demo():
    """Demo the multiple choice component."""
    question = Question(
        text="What is the correct type annotation for a list of strings?",
        options=[
            "list",
            "List[str]",
            "list[str]",
            "str[]"
        ],
        correct_index=2,
        explanation="In Python 3.9+, you can use lowercase 'list[str]'. For older versions, use 'List[str]' from typing module.",
        hint="Python 3.9+ introduced built-in generic types"
    )
    
    mc = MultipleChoice(question)
    is_correct, answer = mc.run()
    print(f"\nDemo complete! Correct: {is_correct}, Selected: {answer}")


if __name__ == "__main__":
    demo()