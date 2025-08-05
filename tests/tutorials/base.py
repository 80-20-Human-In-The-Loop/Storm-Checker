"""
Base Test Class for Storm-Checker Tutorials
============================================
Provides common test functionality for all tutorial tests.
"""

import pytest
from abc import ABC, abstractmethod
from typing import Type, List, Dict, Optional
import re

from storm_checker.tutorials.base_tutorial import BaseTutorial, Question


class BaseTutorialTest(ABC):
    """Base class for testing Storm-Checker tutorials.
    
    Subclasses must implement:
    - tutorial_class: The tutorial class to test
    - expected_id: Expected tutorial ID
    - expected_difficulty_range: Tuple of (min, max) difficulty
    - expected_page_count_range: Tuple of (min, max) page count
    """
    
    @property
    @abstractmethod
    def tutorial_class(self) -> Type[BaseTutorial]:
        """The tutorial class to test."""
        pass
    
    @property
    @abstractmethod
    def expected_id(self) -> str:
        """Expected tutorial ID."""
        pass
    
    @property
    @abstractmethod
    def expected_difficulty_range(self) -> tuple[int, int]:
        """Expected difficulty range (min, max)."""
        pass
    
    @property
    @abstractmethod
    def expected_page_count_range(self) -> tuple[int, int]:
        """Expected page count range (min, max)."""
        pass
    
    @pytest.fixture(scope="class")
    def tutorial(self):
        """Create tutorial instance for testing (cached per test class)."""
        return self.tutorial_class()
    
    # Basic Property Tests
    
    def test_tutorial_has_id(self, tutorial):
        """Test that tutorial has an ID."""
        assert hasattr(tutorial, 'id')
        assert tutorial.id == self.expected_id
        assert isinstance(tutorial.id, str)
        assert len(tutorial.id) > 0
    
    def test_tutorial_has_title(self, tutorial):
        """Test that tutorial has a title."""
        assert hasattr(tutorial, 'title')
        assert isinstance(tutorial.title, str)
        assert len(tutorial.title) > 0
        assert len(tutorial.title) <= 100  # Reasonable title length
    
    def test_tutorial_has_description(self, tutorial):
        """Test that tutorial has a description."""
        assert hasattr(tutorial, 'description')
        assert isinstance(tutorial.description, str)
        assert len(tutorial.description) > 0
        assert len(tutorial.description) <= 200  # Reasonable description length
    
    def test_tutorial_difficulty(self, tutorial):
        """Test that tutorial has valid difficulty."""
        assert hasattr(tutorial, 'difficulty')
        assert isinstance(tutorial.difficulty, int)
        assert 1 <= tutorial.difficulty <= 5
        min_diff, max_diff = self.expected_difficulty_range
        assert min_diff <= tutorial.difficulty <= max_diff
    
    def test_tutorial_estimated_time(self, tutorial):
        """Test that tutorial has reasonable estimated time."""
        assert hasattr(tutorial, 'estimated_minutes')
        assert isinstance(tutorial.estimated_minutes, int)
        assert 1 <= tutorial.estimated_minutes <= 60  # Between 1 min and 1 hour
    
    def test_tutorial_related_errors(self, tutorial):
        """Test that tutorial has related_errors list."""
        assert hasattr(tutorial, 'related_errors')
        assert isinstance(tutorial.related_errors, list)
        for error in tutorial.related_errors:
            assert isinstance(error, str)
            # MyPy error codes are typically lowercase with hyphens
            assert re.match(r'^[a-z-]+$', error), f"Invalid error code format: {error}"
    
    # Page Tests
    
    def test_tutorial_pages_exist(self, tutorial):
        """Test that tutorial has pages."""
        assert hasattr(tutorial, 'pages')
        assert isinstance(tutorial.pages, list)
        min_pages, max_pages = self.expected_page_count_range
        assert min_pages <= len(tutorial.pages) <= max_pages
    
    def test_tutorial_pages_content(self, tutorial):
        """Test that all pages have valid content."""
        for i, page in enumerate(tutorial.pages):
            assert isinstance(page, str), f"Page {i} is not a string"
            assert len(page.strip()) > 0, f"Page {i} is empty"
            assert len(page) <= 5000, f"Page {i} is too long (>5000 chars)"
            # Check that page has at least one heading
            assert '#' in page, f"Page {i} has no markdown headings"
    
    def test_tutorial_pages_markdown_structure(self, tutorial):
        """Test that pages have valid markdown structure."""
        for i, page in enumerate(tutorial.pages):
            lines = page.strip().split('\n')
            # First line should be a heading
            assert lines[0].startswith('#'), f"Page {i} should start with a heading"
            # Check for reasonable line lengths (allowing code blocks)
            for j, line in enumerate(lines):
                if not line.startswith('```') and not line.startswith('    '):
                    assert len(line) <= 120, f"Page {i}, line {j} is too long (>120 chars)"
    
    # Question Tests
    
    def test_tutorial_questions_structure(self, tutorial):
        """Test that tutorial questions have valid structure."""
        assert hasattr(tutorial, 'questions')
        assert isinstance(tutorial.questions, dict)
        
        # Check that question page numbers are valid
        for page_num, question in tutorial.questions.items():
            assert isinstance(page_num, int), f"Question key {page_num} is not an int"
            assert 0 <= page_num < len(tutorial.pages), f"Question on page {page_num} but only {len(tutorial.pages)} pages"
            assert isinstance(question, Question), f"Question on page {page_num} is not a Question object"
    
    def test_tutorial_questions_content(self, tutorial):
        """Test that all questions have valid content."""
        for page_num, question in tutorial.questions.items():
            # Test question text
            assert isinstance(question.text, str)
            assert len(question.text) > 10, f"Question on page {page_num} text too short"
            assert len(question.text) <= 500, f"Question on page {page_num} text too long"
            
            # Test options
            assert isinstance(question.options, list)
            assert 2 <= len(question.options) <= 6, f"Question on page {page_num} should have 2-6 options"
            for opt in question.options:
                assert isinstance(opt, str)
                assert len(opt) > 0
            
            # Test correct index
            assert isinstance(question.correct_index, int)
            assert 0 <= question.correct_index < len(question.options)
            
            # Test explanation
            assert isinstance(question.explanation, str)
            assert len(question.explanation) > 10
            
            # Test hint (optional but should be string if present)
            if question.hint is not None:
                assert isinstance(question.hint, str)
                assert len(question.hint) > 0
    
    def test_tutorial_questions_placement(self, tutorial):
        """Test that questions are placed appropriately."""
        # Questions should not be on the first page (introduction)
        # or last page (usually summary/conclusion)
        for page_num in tutorial.questions.keys():
            assert page_num > 0, "Questions should not be on the first page"
            # Note: Questions CAN be on the last page for final assessment
    
    # Practice Exercise Tests
    
    def test_tutorial_practice_exercise(self, tutorial):
        """Test that practice exercise is valid if present."""
        assert hasattr(tutorial, 'practice_exercise')
        exercise = tutorial.practice_exercise
        
        if exercise is not None:
            assert isinstance(exercise, str)
            assert len(exercise) > 20, "Practice exercise too short"
            assert len(exercise) <= 1000, "Practice exercise too long"
    
    # Integration Tests
    
    def test_tutorial_can_instantiate(self):
        """Test that tutorial can be instantiated."""
        tutorial = self.tutorial_class()
        assert tutorial is not None
        assert isinstance(tutorial, BaseTutorial)
    
    def test_tutorial_has_all_required_properties(self, tutorial):
        """Test that tutorial implements all required properties."""
        required_properties = [
            'id', 'title', 'description', 'difficulty', 
            'estimated_minutes', 'pages', 'questions', 
            'related_errors', 'practice_exercise'
        ]
        
        for prop in required_properties:
            assert hasattr(tutorial, prop), f"Missing required property: {prop}"
    
    def test_tutorial_page_flow(self, tutorial):
        """Test that tutorial pages flow logically."""
        # Check that pages reference concepts in order
        # (This is a basic check - subclasses can override for specific logic)
        pages = tutorial.pages
        
        # First page should introduce the topic
        assert any(word in pages[0].lower() for word in ['introduction', 'understanding', 'learn', 'welcome'])
        
        # Last page should conclude or summarize
        if len(pages) > 1:
            last_page = pages[-1].lower()
            assert any(word in last_page for word in ['summary', 'complete', 'congratulations', 'next', 'practice'])
    
    def test_tutorial_consistent_terminology(self, tutorial):
        """Test that tutorial uses consistent terminology."""
        # Collect all text content
        all_text = tutorial.title + " " + tutorial.description
        for page in tutorial.pages:
            all_text += " " + page
        for question in tutorial.questions.values():
            all_text += " " + question.text + " " + question.explanation
        
        # Check for inconsistent terminology (subclasses can extend)
        # For example, don't mix "MyPy" and "mypy" 
        if "mypy" in all_text.lower():
            # If mypy is mentioned, it should be consistently cased
            assert not ("Mypy" in all_text), "Inconsistent casing: use 'MyPy' or 'mypy' consistently"
    
    def test_tutorial_no_placeholder_text(self, tutorial):
        """Test that tutorial has no placeholder text."""
        placeholder_patterns = [
            "TODO", "FIXME", "XXX", "Lorem ipsum", 
            "placeholder", "coming soon", "TBD"
        ]
        
        all_text = tutorial.title + " " + tutorial.description
        for page in tutorial.pages:
            all_text += " " + page
        
        for pattern in placeholder_patterns:
            assert pattern not in all_text, f"Found placeholder text: {pattern}"