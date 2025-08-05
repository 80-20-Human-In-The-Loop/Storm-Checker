#!/usr/bin/env python3
"""
Tutorial Engine - Core Tutorial Logic
=====================================
Pure business logic for tutorial management without UI concerns.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from pathlib import Path
from datetime import datetime
from .utils import get_data_directory, ensure_directory


class TutorialState(Enum):
    """Current state of the tutorial."""
    WELCOME = "welcome"
    SLIDE_CONTENT = "slide_content"
    QUESTION_PROMPT = "question_prompt"  # Showing "Press Enter for Knowledge Check"
    QUESTION_ACTIVE = "question_active"  # User is answering question
    QUESTION_RESULT = "question_result"  # Showing question result
    COMPLETION = "completion"
    FAILED = "failed"


@dataclass
class TutorialData:
    """Core tutorial data structure."""
    tutorial_id: str
    title: str
    description: str
    pages: List[str]
    questions: Dict[int, Any]  # page_number -> Question object
    difficulty: int
    estimated_minutes: int
    related_errors: List[str]


@dataclass
class TutorialProgress:
    """Tutorial progress tracking."""
    tutorial_id: str
    current_page: int
    pages_completed: int
    total_pages: int
    questions_correct: int
    total_questions: int
    completed: bool
    completion_time: Optional[str] = None
    current_state: TutorialState = TutorialState.WELCOME


class TutorialEngine:
    """Core tutorial engine handling navigation and state management."""
    
    def __init__(self, tutorial_data: TutorialData):
        """Initialize tutorial engine with tutorial data."""
        self.tutorial_data = tutorial_data
        self.progress = self._load_progress()
        self.current_state = TutorialState.WELCOME
        
    def _load_progress(self) -> TutorialProgress:
        """Load existing progress or create new."""
        progress_dir = ensure_directory(get_data_directory() / "tutorial_progress")
        progress_file = progress_dir / f"{self.tutorial_data.tutorial_id}.json"
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    return TutorialProgress(
                        tutorial_id=data['tutorial_id'],
                        current_page=0,  # Always start from beginning
                        pages_completed=0,  # Reset progress
                        total_pages=len(self.tutorial_data.pages),
                        questions_correct=0,  # Reset score
                        total_questions=len(self.tutorial_data.questions),
                        completed=data.get('completed', False),  # Keep completion status
                        completion_time=data.get('completion_time'),
                        current_state=TutorialState.WELCOME  # Reset state
                    )
            except Exception:
                pass
                
        # Create new progress
        return TutorialProgress(
            tutorial_id=self.tutorial_data.tutorial_id,
            current_page=0,
            pages_completed=0,
            total_pages=len(self.tutorial_data.pages),
            questions_correct=0,
            total_questions=len(self.tutorial_data.questions),
            completed=False,
            current_state=TutorialState.WELCOME
        )
        
    def save_progress(self) -> None:
        """Save current progress to disk."""
        progress_dir = ensure_directory(get_data_directory() / "tutorial_progress")
        progress_file = progress_dir / f"{self.tutorial_data.tutorial_id}.json"
        
        progress_data = {
            'tutorial_id': self.progress.tutorial_id,
            'current_page': self.progress.current_page,
            'pages_completed': self.progress.pages_completed,
            'total_pages': self.progress.total_pages,
            'questions_correct': self.progress.questions_correct,
            'total_questions': self.progress.total_questions,
            'completed': self.progress.completed,
            'completion_time': self.progress.completion_time,
            'current_state': self.progress.current_state.value
        }
        
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
            
    def can_resume(self) -> bool:
        """Check if tutorial can be resumed from previous progress."""
        return self.progress.pages_completed > 0 and not self.progress.completed
        
    def resume_from_saved(self) -> None:
        """Resume tutorial from saved progress."""
        self.progress.current_page = self.progress.pages_completed
        
    def get_current_page_data(self) -> Optional[Dict[str, Any]]:
        """Get current page data."""
        if self.progress.current_page >= len(self.tutorial_data.pages):
            return None
            
        page_number = self.progress.current_page
        return {
            'page_number': page_number,
            'slide_number': page_number + 1,
            'total_slides': len(self.tutorial_data.pages),
            'title': self._extract_page_title(page_number),
            'content': self.tutorial_data.pages[page_number],
            'has_question': page_number in self.tutorial_data.questions,
            'question': self.tutorial_data.questions.get(page_number)
        }
        
    def _extract_page_title(self, page_number: int) -> str:
        """Extract title from page content."""
        content = self.tutorial_data.pages[page_number]
        lines = content.strip().split('\n')
        
        # Look for markdown heading
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
                
        # Fallback titles
        if page_number == 0:
            return "Introduction"
        elif page_number == len(self.tutorial_data.pages) - 1:
            return "Summary"
        else:
            return f"Part {page_number + 1}"
            
    def can_go_next(self) -> bool:
        """Check if can advance to next page."""
        return self.progress.current_page < len(self.tutorial_data.pages) - 1
        
    def can_go_back(self) -> bool:
        """Check if can go to previous page."""
        return self.progress.current_page > 0
        
    def go_next(self) -> bool:
        """Advance to next page. Returns True if successful."""
        if self.can_go_next():
            self.progress.current_page += 1
            self.progress.pages_completed = max(
                self.progress.pages_completed, 
                self.progress.current_page
            )
            self.current_state = TutorialState.SLIDE_CONTENT
            return True
        return False
        
    def go_back(self) -> bool:
        """Go to previous page. Returns True if successful."""
        if self.can_go_back():
            self.progress.current_page -= 1
            self.current_state = TutorialState.SLIDE_CONTENT
            return True
        return False
        
    def start_question(self) -> None:
        """Transition to question state."""
        self.current_state = TutorialState.QUESTION_ACTIVE
        
    def complete_question(self, is_correct: bool) -> bool:
        """
        Complete question and return whether tutorial can continue.
        
        Returns:
            True if tutorial can continue, False if should exit
        """
        page_number = self.progress.current_page
        
        if is_correct:
            self.progress.questions_correct += 1
            self.current_state = TutorialState.QUESTION_RESULT
            return True
        else:
            # Failed question
            if page_number < len(self.tutorial_data.pages) - 1:
                # Mid-tutorial question failed - boot out
                self.current_state = TutorialState.FAILED
                return False
            else:
                # Final question - can still continue
                self.current_state = TutorialState.QUESTION_RESULT
                return True
                
    def is_tutorial_complete(self) -> bool:
        """Check if tutorial is complete."""
        return self.progress.current_page >= len(self.tutorial_data.pages) - 1
        
    def complete_tutorial(self) -> None:
        """Mark tutorial as completed."""
        self.progress.completed = True
        self.progress.completion_time = datetime.now().isoformat()
        self.current_state = TutorialState.COMPLETION
        self.save_progress()
        
        # Update global progress tracker
        try:
            from logic.progress_tracker import ProgressTracker
            tracker = ProgressTracker()
            tracker.update_tutorial_progress(self.tutorial_data.tutorial_id, 100.0)
        except Exception:
            # Don't break tutorial if progress tracking fails
            pass
        
    def get_completion_data(self) -> Dict[str, Any]:
        """Get completion data for display."""
        score_pct = (
            (self.progress.questions_correct / self.progress.total_questions * 100) 
            if self.progress.total_questions > 0 else 0
        )
        
        return {
            'tutorial_id': self.tutorial_data.tutorial_id,
            'title': self.tutorial_data.title,
            'score': (self.progress.questions_correct, self.progress.total_questions),
            'score_percentage': score_pct,
            'related_errors': self.tutorial_data.related_errors
        }