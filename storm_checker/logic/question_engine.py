#!/usr/bin/env python3
"""
Question Engine - Pure Question Logic
=====================================
Handles question logic without UI concerns.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum


class QuestionState(Enum):
    """Current state of a question."""
    DISPLAYING = "displaying"
    ANSWERED = "answered"


@dataclass
class Question:
    """Question data structure."""
    text: str
    options: List[str]
    correct_index: int
    explanation: Optional[str] = None
    hint: Optional[str] = None


class QuestionEngine:
    """Handles question logic and validation."""
    
    def __init__(self, question: Question):
        """Initialize with question data."""
        self.question = question
        self.selected_index = 0
        self.state = QuestionState.DISPLAYING
        self.user_answer: Optional[int] = None
        
    def get_selected_index(self) -> int:
        """Get currently selected option index."""
        return self.selected_index
        
    def can_move_up(self) -> bool:
        """Check if can move selection up."""
        return self.selected_index > 0
        
    def can_move_down(self) -> bool:
        """Check if can move selection down."""
        return self.selected_index < len(self.question.options) - 1
        
    def move_up(self) -> bool:
        """Move selection up. Returns True if moved."""
        if self.can_move_up():
            self.selected_index -= 1
            return True
        return False
        
    def move_down(self) -> bool:
        """Move selection down. Returns True if moved."""
        if self.can_move_down():
            self.selected_index += 1
            return True
        return False
        
    def select_by_number(self, number: int) -> bool:
        """Select option by number (1-based). Returns True if valid."""
        index = number - 1
        if 0 <= index < len(self.question.options):
            self.selected_index = index
            return True
        return False
        
    def submit_answer(self) -> Tuple[bool, int]:
        """
        Submit current selection as answer.
        
        Returns:
            Tuple of (is_correct, selected_index)
        """
        self.user_answer = self.selected_index
        self.state = QuestionState.ANSWERED
        is_correct = self.user_answer == self.question.correct_index
        return (is_correct, self.user_answer)
        
    def is_answered(self) -> bool:
        """Check if question has been answered."""
        return self.state == QuestionState.ANSWERED
        
    def get_result_data(self) -> Optional[dict]:
        """Get result data after question is answered."""
        if not self.is_answered():
            return None
            
        is_correct = self.user_answer == self.question.correct_index
        
        return {
            'is_correct': is_correct,
            'user_answer': self.user_answer,
            'correct_answer': self.question.correct_index,
            'correct_option': self.question.options[self.question.correct_index],
            'user_option': self.question.options[self.user_answer] if self.user_answer is not None else None,
            'explanation': self.question.explanation
        }
        
    def get_display_data(self) -> dict:
        """Get data needed for question display."""
        return {
            'question_text': self.question.text,
            'options': self.question.options,
            'selected_index': self.selected_index,
            'hint': self.question.hint if not self.is_answered() else None,
            'is_answered': self.is_answered(),
            'user_answer': self.user_answer,
            'correct_index': self.question.correct_index
        }
        
    def reset(self) -> None:
        """Reset question to initial state."""
        self.selected_index = 0
        self.state = QuestionState.DISPLAYING
        self.user_answer = None