#!/usr/bin/env python3
"""
Base Tutorial Framework for Storm-Checker Educational System
===========================================================
Provides the foundation for creating interactive, multi-page tutorials
that teach Python type safety concepts through hands-on learning.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path
from datetime import datetime

from logic.progress_tracker import ProgressTracker

# Import our system components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.user_input.multiple_choice import MultipleChoice, Question
from cli.components.slideshow import Slideshow, Slide, ContentMode
from cli.colors import THEME, RESET, BOLD, CLEAR_SCREEN, CURSOR_HIDE, CURSOR_SHOW
from logic.utils import get_data_directory, ensure_directory

# Legacy color mappings for compatibility
LEARN_BLUE = THEME["learn"].ansi
LEARN_GREEN = THEME["success"].ansi
LEARN_YELLOW = THEME["warning"].ansi
LEARN_PURPLE = THEME["accent"].ansi
LEARN_CYAN = THEME["info"].ansi


@dataclass
class TutorialProgress:
    """Track user's progress through tutorials."""
    tutorial_id: str
    pages_completed: int
    total_pages: int
    questions_correct: int
    total_questions: int
    completed: bool
    completion_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tutorial_id": self.tutorial_id,
            "pages_completed": self.pages_completed,
            "total_pages": self.total_pages,
            "questions_correct": self.questions_correct,
            "total_questions": self.total_questions,
            "completed": self.completed,
            "completion_time": self.completion_time
        }


class BaseTutorial(ABC):
    """
    Abstract base class for all Storm-Checker tutorials.
    
    Each tutorial should:
    - Have 3-5 pages of educational content
    - Include at least one question halfway through
    - Include a final question to test understanding
    - Provide practical code examples
    - Link to relevant MyPy error types
    """
    
    def __init__(self):
        self.tutorial_id = self.id
        self.progress_dir = ensure_directory(get_data_directory() / "tutorial_progress")
        self.current_page = 0
        self.progress = self.load_progress()
        self.slideshow = Slideshow()
        
    @property
    @abstractmethod
    def title(self) -> str:
        """Tutorial title displayed to users."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what this tutorial teaches."""
        pass
        
    @property
    @abstractmethod
    def pages(self) -> List[str]:
        """List of tutorial pages (3-5 pages of content)."""
        pass
        
    @property
    @abstractmethod
    def questions(self) -> Dict[int, Question]:
        """
        Questions mapped to page numbers where they should appear.
        E.g., {2: question1, 4: question2} shows questions after pages 2 and 4.
        """
        pass
        
    @property
    def related_errors(self) -> List[str]:
        """List of MyPy error codes this tutorial helps with."""
        return []  # Override in subclasses if needed
        
    @property
    def id(self) -> str:
        """Unique identifier for this tutorial."""
        return self.__class__.__name__.lower().replace("tutorial", "")
        
    @property
    def difficulty(self) -> int:
        """Difficulty level from 1-5."""
        return 1  # Override in subclasses
        
    @property
    def estimated_minutes(self) -> int:
        """Estimated time to complete in minutes."""
        return 10  # Override in subclasses
        
    def load_progress(self) -> TutorialProgress:
        """Load saved progress for this tutorial."""
        progress_file = self.progress_dir / f"{self.tutorial_id}.json"
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    return TutorialProgress(**data)
            except Exception:
                pass
                
        # Return fresh progress if none exists
        return TutorialProgress(
            tutorial_id=self.tutorial_id,
            pages_completed=0,
            total_pages=len(self.pages),
            questions_correct=0,
            total_questions=len(self.questions),
            completed=False
        )
        
    def save_progress(self) -> None:
        """Save current progress to disk and update global progress tracker."""
        progress_file = self.progress_dir / f"{self.tutorial_id}.json"
        
        with open(progress_file, 'w') as f:
            json.dump(self.progress.to_dict(), f, indent=2)
        
        # Update global progress tracker
        try:
            tracker = ProgressTracker()
            completion_percentage = (self.progress.pages_completed / self.progress.total_pages) * 100
            tracker.update_tutorial_progress(self.tutorial_id, completion_percentage)
        except Exception:
            # Don't break tutorial if progress tracking fails
            pass
            
    def display_header(self) -> None:
        """Display tutorial header with progress."""
        print(CLEAR_SCREEN)
        print(f"{LEARN_BLUE}{'═' * 60}{RESET}")
        print(f"{LEARN_CYAN}{BOLD}📚 {self.title}{RESET}")
        print(f"{LEARN_PURPLE}{self.description}{RESET}")
        print(f"{LEARN_BLUE}{'═' * 60}{RESET}")
        
        # Progress bar
        progress_pct = (self.current_page / len(self.pages)) * 100
        filled = int(progress_pct / 5)  # 20 character progress bar
        bar = "█" * filled + "░" * (20 - filled)
        print(f"\nProgress: [{LEARN_GREEN}{bar}{RESET}] {progress_pct:.0f}%")
        print(f"Page {self.current_page + 1} of {len(self.pages)}\n")
        
    def display_page(self, page_number: int) -> bool:
        """Display a specific page of the tutorial using buffer-based approach.
        
        Returns:
            True if user can continue, False if they failed a question
        """
        if page_number >= len(self.pages):
            return True
            
        # Create slide
        slide = Slide(
            title=self._get_page_title(page_number),
            content=self.pages[page_number],
            slide_number=page_number + 1,
            total_slides=len(self.pages),
            tutorial_id=self.tutorial_id,
            has_question=page_number in self.questions
        )
        
        # Step 1: Show slide content (with question prompt if needed)
        nav_hints = f"{THEME['info']}[Enter: Next | b: Back | q: Quit]{RESET}"
        if slide.has_question:
            nav_hints = f"{THEME['warning']}[Enter: Knowledge Check | b: Back | q: Quit]{RESET}"
            
        print(self.slideshow.render_dynamic_content(
            slide, 
            ContentMode.SLIDE, 
            is_completed=self.progress.completed, 
            navigation_hints=nav_hints
        ))
        
        # If there's a question, handle the interactive flow
        if page_number in self.questions:
            # Wait for user to press Enter for knowledge check
            print(f"\n{THEME['info']}Press Enter for Knowledge Check, 'b' to go back, or 'q' to quit:{RESET}")
            choice = input().strip().lower()
            
            if choice == 'q':
                return False
            elif choice == 'b':
                return True  # Let navigation handle going back
            
            # Step 2: Switch to question mode within same slideshow buffer
            question = self.questions[page_number]
            question_nav_hints = f"{THEME['warning']}Knowledge Check in progress...{RESET}"
            
            print(self.slideshow.render_dynamic_content(
                slide,
                ContentMode.QUESTION,
                is_completed=self.progress.completed,
                navigation_hints=question_nav_hints
            ))
            
            # Step 3: Run question within the slideshow buffer
            mc = MultipleChoice(question, integrated_mode=True)
            is_correct, _ = mc.run()
            
            # Step 4: Show result within slideshow buffer
            if is_correct:
                self.progress.questions_correct += 1
                result_content = f"{THEME['success']}✅ Correct! Well done!{RESET}\n\nPress Enter to continue..."
            else:
                result_content = f"{THEME['error']}❌ Not quite right.{RESET}\n\n"
                result_content += f"The correct answer is: {question.options[question.correct_index]}\n\n"
                if question.explanation:
                    result_content += f"📖 Explanation: {question.explanation}\n\n"
                
                # Boot out on failure for mid-tutorial questions!
                if page_number < len(self.pages) - 1:
                    result_content += f"{THEME['warning']}You need to master this concept before continuing.{RESET}\n"
                    result_content += "The tutorial will restart. Press Enter to exit..."
                    
            print(self.slideshow.render_dynamic_content(
                slide,
                ContentMode.RESULT,
                content_data=result_content,
                is_completed=self.progress.completed,
                navigation_hints=f"{THEME['info']}Press Enter to continue...{RESET}"
            ))
            
            input()  # Wait for user acknowledgment
            
            # Boot out if failed mid-tutorial question
            if not is_correct and page_number < len(self.pages) - 1:
                return False
                    
        return True
                
    def display_completion(self) -> None:
        """Display tutorial completion screen."""
        score_pct = (self.progress.questions_correct / self.progress.total_questions) * 100 if self.progress.total_questions > 0 else 0
        
        # Create completion message
        message_lines = []
        message_lines.append(f"Your Score: {self.progress.questions_correct}/{self.progress.total_questions} ({score_pct:.0f}%)")
        
        if score_pct >= 80:
            message_lines.append(f"Excellent work! You've mastered {self.title}!")
        elif score_pct >= 60:
            message_lines.append("Good job! Consider reviewing the concepts you missed.")
        else:
            message_lines.append("Keep practicing! You might want to review this tutorial again.")
            
        # Show related MyPy errors
        if self.related_errors:
            message_lines.append("")
            message_lines.append("This tutorial helps with these MyPy errors:")
            for error in self.related_errors:
                message_lines.append(f"  • {error}")
                
        message = "\n".join(message_lines)
        
        # TODO: Add achievement unlocking here
        achievements = ["🎯 Tutorial Complete"]
        
        # Use slideshow completion screen
        completion_screen = self.slideshow.render_completion_screen(
            self.tutorial_id,
            (self.progress.questions_correct, self.progress.total_questions),
            message,
            achievements
        )
        
        print(completion_screen)
        
    def run(self) -> None:
        """Run the interactive tutorial using new architecture."""
        # Import the new controller
        from cli.interactive.tutorial_controller import TutorialController
        from logic.tutorial_engine import TutorialData
        from logic.question_engine import Question as NewQuestion
        
        # Convert old questions to new format
        new_questions = {}
        for page_num, old_question in self.questions.items():
            new_questions[page_num] = NewQuestion(
                text=old_question.text,
                options=old_question.options,
                correct_index=old_question.correct_index,
                explanation=old_question.explanation,
                hint=old_question.hint
            )
        
        # Create tutorial data for new system
        tutorial_data = TutorialData(
            tutorial_id=self.tutorial_id,
            title=self.title,
            description=self.description,
            pages=self.pages,
            questions=new_questions,
            difficulty=self.difficulty,
            estimated_minutes=self.estimated_minutes,
            related_errors=self.related_errors
        )
        
        # Use new controller
        controller = TutorialController(tutorial_data)
        controller.run()
        
    def _get_page_title(self, page_number: int) -> str:
        """Extract or generate a title for the current page."""
        content = self.pages[page_number]
        lines = content.strip().split('\n')
        
        # Look for a markdown heading
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
                
        # Fallback to generic title
        if page_number == 0:
            return "Introduction"
        elif page_number == len(self.pages) - 1:
            return "Summary"
        else:
            return f"Part {page_number + 1}"
            
    @classmethod
    def get_tutorial_for_error(cls, error_code: str) -> Optional[str]:
        """
        Get recommended tutorial for a specific MyPy error code.
        This will be overridden by a registry system later.
        """
        # TODO: Implement tutorial registry/recommendation system
        return None
        

# TODO: Create tutorial registry for automatic recommendations
# TODO: Add tutorial prerequisites system
# TODO: Add tutorial difficulty levels (beginner, intermediate, advanced)
# TODO: Add interactive code exercises within tutorials
# TODO: Add progress achievements and badges