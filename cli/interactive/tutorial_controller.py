#!/usr/bin/env python3
"""
Tutorial Controller - Coordination Layer
========================================
Coordinates tutorial engine, renderers, and user interaction.
"""

import sys
import termios
import tty  
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.colors import THEME, RESET
from cli.components.tutorial_renderer import TutorialRenderer
from cli.components.question_renderer import QuestionRenderer
from logic.tutorial_engine import TutorialEngine, TutorialState, TutorialData
from logic.question_engine import QuestionEngine


class TutorialController:
    """Coordinates tutorial execution with clean separation of concerns."""
    
    def __init__(self, tutorial_data: TutorialData):
        """Initialize controller with tutorial data."""
        self.engine = TutorialEngine(tutorial_data)
        self.renderer = TutorialRenderer()
        self.question_renderer = QuestionRenderer()
        self.current_question_engine: Optional[QuestionEngine] = None
        
    def run(self) -> None:
        """Run the complete tutorial experience."""
        try:
            # Welcome screen
            self._show_welcome()
            
            # Always start from the beginning
            # (Progress tracking is still saved for completion status)
                    
            # Main tutorial loop
            while True:
                page_data = self.engine.get_current_page_data()
                if not page_data:
                    break
                    
                # Show slide content
                if not self._display_slide_content(page_data):
                    break  # User quit
                    
                # Handle question if present
                if page_data['has_question']:
                    if not self._handle_question(page_data):
                        break  # User quit or failed
                    # After successful question, check if tutorial is complete
                    if self.engine.is_tutorial_complete():
                        self.engine.complete_tutorial()
                        self._show_completion()
                        break
                    # Otherwise auto-advance to next page
                    self.engine.go_next()
                    continue  # Skip navigation prompt
                        
                # Check if tutorial complete (for non-question pages)
                if self.engine.is_tutorial_complete():
                    self.engine.complete_tutorial()
                    self._show_completion()
                    break
                    
                # Navigation (only shown if no question was answered)
                if not self._handle_navigation():
                    break  # User quit
                    
        except KeyboardInterrupt:
            print(f"\n{THEME['warning']}Tutorial interrupted.{RESET}")
            self.engine.save_progress()
            
    def _show_welcome(self) -> None:
        """Show tutorial welcome screen."""
        welcome_data = {
            'title': self.engine.tutorial_data.title,
            'description': self.engine.tutorial_data.description
        }
        
        welcome_screen = self.renderer.render_welcome_screen(welcome_data)
        print(welcome_screen)
        input()  # Wait for Enter
        
    def _ask_resume(self) -> bool:
        """Ask user if they want to resume."""
        print(f"\n{THEME['warning']}You have previous progress in this tutorial.{RESET}")
        choice = input("Resume from where you left off? [Y/n]: ").strip().lower()
        return choice != 'n'
        
    def _display_slide_content(self, page_data: dict) -> bool:
        """Display slide content and handle basic navigation."""
        tutorial_data = {
            'tutorial_id': self.engine.tutorial_data.tutorial_id,
            'completed': self.engine.progress.completed
        }
        
        # Show slide with question prompt if needed
        slide_screen = self.renderer.render_slide_content(
            tutorial_data,
            page_data,
            show_question_prompt=page_data['has_question']
        )
        print(slide_screen)
        
        return True
        
    def _handle_question(self, page_data: dict) -> bool:
        """Handle question interaction within slideshow buffer."""
        # Wait for user to press Enter for knowledge check
        choice = input().strip().lower()
        
        if choice == 'q':
            return False
        elif choice == 'b':
            return True  # Let navigation handle going back
            
        # Show question screen
        tutorial_data = {
            'tutorial_id': self.engine.tutorial_data.tutorial_id,
            'completed': self.engine.progress.completed
        }
        
        # Create question engine and get formatted content
        question = page_data['question']
        self.current_question_engine = QuestionEngine(question)
        question_data = self.current_question_engine.get_display_data()
        question_content = self.question_renderer.format_complete_question(question_data)
        
        # Render question screen with integrated content
        question_screen = self.renderer.render_question_screen(
            tutorial_data, 
            page_data,
            question_content
        )
        print(question_screen)
        
        # Handle question input
        is_correct = self._run_question_input()
        
        # Process answer
        can_continue = self.engine.complete_question(is_correct)
        
        # Show result
        result_data = self.current_question_engine.get_result_data()
        if result_data:
            result_screen = self.renderer.render_result_screen(
                tutorial_data, 
                page_data, 
                result_data
            )
            print(result_screen)
            
            # Handle failure case
            if not can_continue:
                print(f"\n{THEME['error']}⚠️  TUTORIAL FAILED - Mid-tutorial questions must be answered correctly!{RESET}")
                print(f"{THEME['warning']}You need to master this concept before continuing.{RESET}")
                print(f"\n{THEME['info']}To try again, run: stormcheck tutorial {self.engine.tutorial_data.tutorial_id}{RESET}")
                print("\nPress Enter to exit...")
                input()
                return False
                
            input()  # Wait for acknowledgment
            
        return True
        
    def _run_question_input(self) -> bool:
        """Handle question input interaction."""
        if not self.current_question_engine:
            return False
            
        while not self.current_question_engine.is_answered():
            key = self._get_key()
            
            if key == 'UP' and self.current_question_engine.move_up():
                self._refresh_question_display()
            elif key == 'DOWN' and self.current_question_engine.move_down():
                self._refresh_question_display()
            elif key in '123456789':
                number = int(key)
                if self.current_question_engine.select_by_number(number):
                    is_correct, _ = self.current_question_engine.submit_answer()
                    return is_correct
            elif key == 'ENTER':
                is_correct, _ = self.current_question_engine.submit_answer()
                return is_correct
            elif key == 'QUIT':
                return False
                
        return False
        
    def _refresh_question_display(self) -> None:
        """Refresh question display after selection change."""
        if not self.current_question_engine:
            return
            
        question_data = self.current_question_engine.get_display_data()
        question_content = self.question_renderer.format_complete_question(question_data)
        
        # Simple approach: clear and redisplay
        print("\033[2J\033[H", end="")  # Clear screen
        
        # Re-render question screen with integrated content
        tutorial_data = {
            'tutorial_id': self.engine.tutorial_data.tutorial_id,
            'completed': self.engine.progress.completed
        }
        page_data = self.engine.get_current_page_data()
        if page_data:
            question_screen = self.renderer.render_question_screen(
                tutorial_data, 
                page_data,
                question_content
            )
            print(question_screen)
        
    def _get_key(self) -> str:
        """Get single keypress from user."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
            
            # Handle special keys (arrow keys)
            if key == '\x1b':  # ESC sequence
                key += sys.stdin.read(2)
                if key == '\x1b[A':  # Up arrow
                    return 'UP'
                elif key == '\x1b[B':  # Down arrow
                    return 'DOWN'
            elif key in '123456789':
                return key
            elif key == '\r' or key == '\n':  # Enter
                return 'ENTER'
            elif key == 'q' or key == '\x03':  # q or Ctrl+C
                return 'QUIT'
                
            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    def _handle_navigation(self) -> bool:
        """Handle tutorial navigation."""
        choice = input().strip().lower()
        
        if choice == 'q':
            self.engine.save_progress()
            return False
        elif choice == 'b':
            self.engine.go_back()
        else:
            self.engine.go_next()
            
        return True
        
    def _show_completion(self) -> None:
        """Show tutorial completion screen."""
        completion_data = self.engine.get_completion_data()
        completion_screen = self.renderer.render_completion_screen(completion_data)
        print(completion_screen)
        input()  # Wait for key press