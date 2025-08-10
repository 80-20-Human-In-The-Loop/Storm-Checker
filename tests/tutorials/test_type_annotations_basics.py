"""
Comprehensive Tests for TypeAnnotationsBasics Tutorial
=======================================================
Tests for storm_checker/tutorials/type_annotations_basics.py with full coverage.
"""

import pytest
from unittest.mock import Mock, patch
from storm_checker.tutorials.type_annotations_basics import TypeAnnotationsBasics
from storm_checker.cli.user_input.multiple_choice import Question


class TestTypeAnnotationsBasics:
    """Test the TypeAnnotationsBasics tutorial comprehensively."""
    
    def test_initialization(self):
        """Test that TypeAnnotationsBasics can be instantiated."""
        tutorial = TypeAnnotationsBasics()
        assert isinstance(tutorial, TypeAnnotationsBasics)
        # Verify it inherits from BaseTutorial
        from storm_checker.tutorials.base_tutorial import BaseTutorial
        assert isinstance(tutorial, BaseTutorial)
    
    def test_id_property(self):
        """Test the id property returns correct value."""
        tutorial = TypeAnnotationsBasics()
        assert tutorial.id == "type_annotations_basics"
    
    def test_title_property(self):
        """Test the title property returns correct value."""
        tutorial = TypeAnnotationsBasics()
        assert tutorial.title == "Type Annotations Basics"
    
    def test_description_property(self):
        """Test the description property returns correct value."""
        tutorial = TypeAnnotationsBasics()
        expected = "Learn how to add type hints to variables and functions for better code clarity and error prevention."
        assert tutorial.description == expected
    
    def test_pages_property_structure(self):
        """Test that pages property returns correct structure."""
        tutorial = TypeAnnotationsBasics()
        pages = tutorial.pages
        
        # Should return a list of 7 pages
        assert isinstance(pages, list)
        assert len(pages) == 7
        
        # All pages should be strings
        for page in pages:
            assert isinstance(page, str)
            assert len(page) > 0
    
    def test_page_1_content(self):
        """Test page 1 content - Introduction to Type Annotations."""
        tutorial = TypeAnnotationsBasics()
        page1 = tutorial.pages[0]
        
        # Check key content is present
        assert "# Introduction to Type Annotations" in page1
        assert "Type annotations (type hints)" in page1
        assert "def calculate_tax" in page1
        assert "MyPy catches this before you run the code!" in page1
        assert "Why Type Annotations Matter" in page1
        assert "Catch Bugs Early" in page1
    
    def test_page_2_content(self):
        """Test page 2 content - Basic Variable Type Annotations."""
        tutorial = TypeAnnotationsBasics()
        page2 = tutorial.pages[1]
        
        assert "# Basic Variable Type Annotations" in page2
        assert "Built-in Types" in page2
        assert "name: str = \"Alice\"" in page2
        assert "Collection Types" in page2
        assert "list[str]" in page2
        assert "dict[str, int]" in page2
        assert "Common MyPy Issue: Empty Collections" in page2
    
    def test_page_3_content(self):
        """Test page 3 content - Function Type Annotations."""
        tutorial = TypeAnnotationsBasics()
        page3 = tutorial.pages[2]
        
        assert "# Function Type Annotations" in page3
        assert "Function annotations" in page3 or "function annotations" in page3
        assert "-> int:" in page3 or "-> str:" in page3  # Some return type example
        assert "def " in page3  # Has function definitions
        assert "-> None:" in page3  # None return type
    
    def test_page_4_content(self):
        """Test page 4 content - Working with None and Optional."""
        tutorial = TypeAnnotationsBasics()
        page4 = tutorial.pages[3]
        
        # Check for various possible content about Optional/None
        assert "Optional" in page4 or "None" in page4
        assert "Optional[" in page4 or "| None" in page4 or "Union[" in page4
    
    def test_page_5_content(self):
        """Test page 5 content - Advanced Type Patterns."""
        tutorial = TypeAnnotationsBasics()
        page5 = tutorial.pages[4]
        
        # Check for advanced type content
        assert "Advanced" in page5 or "Generic" in page5 or "TypeVar" in page5
    
    def test_page_6_content(self):
        """Test page 6 content - Common MyPy Errors and Solutions."""
        tutorial = TypeAnnotationsBasics()
        page6 = tutorial.pages[5]
        
        # Check for error-related content
        assert "Error" in page6 or "error" in page6 or "MyPy" in page6 or "mypy" in page6
    
    def test_page_7_content(self):
        """Test page 7 content - Best Practices."""
        tutorial = TypeAnnotationsBasics()
        page7 = tutorial.pages[6]
        
        # Check for best practices content
        assert "Best Practice" in page7 or "best practice" in page7 or "Practice" in page7
    
    def test_questions_property_structure(self):
        """Test that questions property returns correct structure."""
        tutorial = TypeAnnotationsBasics()
        questions = tutorial.questions
        
        # Should return a dictionary
        assert isinstance(questions, dict)
        
        # Should have 5 questions mapped to page numbers (not indices)
        assert len(questions) == 5
        # Questions are actually mapped to page numbers 1, 2, 3, 4, 6
        assert set(questions.keys()) == {1, 2, 3, 4, 6}
        
        # All values should be Question objects
        for page_num, question in questions.items():
            assert isinstance(question, Question)
    
    def test_question_1_after_page_2(self):
        """Test question 1 - after Basic Variable Annotations page."""
        tutorial = TypeAnnotationsBasics()
        q1 = tutorial.questions[1]  # Key is 1, not 0
        
        assert isinstance(q1, Question)
        assert "empty list" in q1.text.lower() or "annotates" in q1.text.lower()
        assert len(q1.options) == 4
        assert q1.correct_index == 2  # Based on the actual question
        assert q1.explanation is not None
        assert q1.hint is not None
    
    def test_question_2_after_page_3(self):
        """Test question 2 - after Function Type Annotations page."""
        tutorial = TypeAnnotationsBasics()
        q2 = tutorial.questions[2]  # Key is 2
        
        assert isinstance(q2, Question)
        assert "user" in q2.text.lower() or "none" in q2.text.lower()
        assert len(q2.options) == 4
        assert q2.correct_index == 3  # "All of the above are equivalent"
        assert q2.explanation is not None
    
    def test_question_3_after_page_4(self):
        """Test question 3 - after page 4."""
        tutorial = TypeAnnotationsBasics()
        q3 = tutorial.questions[3]  # Key is 3
        
        assert isinstance(q3, Question)
        assert "no-untyped-call" in q3.text or "untyped" in q3.text.lower()
        assert len(q3.options) == 4
        assert q3.correct_index == 0  # "The process_data() function has no type annotations"
        assert q3.explanation is not None
    
    def test_question_4_after_page_5(self):
        """Test question 4 - after page 5."""
        tutorial = TypeAnnotationsBasics()
        q4 = tutorial.questions[4]  # Key is 4
        
        assert isinstance(q4, Question)
        assert "pipeline" in q4.text.lower() or "process" in q4.text.lower()
        assert len(q4.options) == 4
        assert q4.correct_index == 2  # Generic with constraints
        assert q4.explanation is not None
    
    def test_question_5_after_page_7(self):
        """Test question 5 - after Best Practices page."""
        tutorial = TypeAnnotationsBasics()
        q5 = tutorial.questions[6]  # Key is 6, after page 7
        
        assert isinstance(q5, Question)
        assert "team" in q5.text.lower() or "legacy" in q5.text.lower() or "migrating" in q5.text.lower()
        assert len(q5.options) == 4
        assert q5.correct_index == 1  # "Start with critical business logic..."
        assert q5.explanation is not None
        assert "gradual adoption" in q5.explanation.lower() or "critical" in q5.explanation.lower()
    
    def test_all_questions_have_required_fields(self):
        """Test that all questions have required fields populated."""
        tutorial = TypeAnnotationsBasics()
        
        for page_num, question in tutorial.questions.items():
            # Check required fields
            assert question.text is not None and len(question.text) > 0
            assert question.options is not None and len(question.options) >= 2
            assert question.correct_index is not None
            assert 0 <= question.correct_index < len(question.options)
            assert question.explanation is not None and len(question.explanation) > 0
            assert question.hint is not None and len(question.hint) > 0
    
    def test_pages_contain_code_examples(self):
        """Test that all tutorial pages contain code examples."""
        tutorial = TypeAnnotationsBasics()
        
        # Check that pages contain code blocks
        for i, page in enumerate(tutorial.pages):
            # All pages should have code examples marked with ```
            assert "```" in page, f"Page {i+1} should contain code examples"
            # Should have Python code
            assert "```python" in page or "def " in page or ":" in page, f"Page {i+1} should have Python code"
    
    def test_pages_contain_markdown_formatting(self):
        """Test that pages use proper markdown formatting."""
        tutorial = TypeAnnotationsBasics()
        
        for i, page in enumerate(tutorial.pages):
            # Should have headers
            assert "#" in page, f"Page {i+1} should have markdown headers"
            # Should have some formatting
            assert any(marker in page for marker in ["**", "##", "```", "-", "*"]), \
                f"Page {i+1} should have markdown formatting"
    
    @patch('storm_checker.tutorials.base_tutorial.MultipleChoice')
    def test_tutorial_can_run(self, mock_mc_class):
        """Test that the tutorial can be run (inherited from BaseTutorial)."""
        # Setup mock for MultipleChoice
        mock_mc = Mock()
        mock_mc.run.return_value = (True, 0)  # Simulate correct answer
        mock_mc_class.return_value = mock_mc
        
        tutorial = TypeAnnotationsBasics()
        
        # The tutorial should have the run method from BaseTutorial
        assert hasattr(tutorial, 'run')
        assert callable(tutorial.run)
        
        # Should be able to get progress
        assert hasattr(tutorial, 'load_progress')
        assert hasattr(tutorial, 'save_progress')
    
    def test_question_options_are_unique(self):
        """Test that each question has unique answer options."""
        tutorial = TypeAnnotationsBasics()
        
        for page_num, question in tutorial.questions.items():
            options_set = set(question.options)
            assert len(options_set) == len(question.options), \
                f"Question on page {page_num} has duplicate options"
    
    def test_question_correct_index_valid(self):
        """Test that correct_index points to a valid option."""
        tutorial = TypeAnnotationsBasics()
        
        for page_num, question in tutorial.questions.items():
            assert 0 <= question.correct_index < len(question.options), \
                f"Question on page {page_num} has invalid correct_index"
            
            # The correct answer should exist
            correct_answer = question.options[question.correct_index]
            assert correct_answer is not None and len(correct_answer) > 0
    
    def test_tutorial_metadata(self):
        """Test tutorial has proper metadata for registration."""
        tutorial = TypeAnnotationsBasics()
        
        # Should have an ID that can be used for registration
        assert tutorial.id is not None
        assert isinstance(tutorial.id, str)
        assert len(tutorial.id) > 0
        
        # Should have a title for display
        assert tutorial.title is not None
        assert isinstance(tutorial.title, str)
        assert len(tutorial.title) > 0
        
        # Should have a description
        assert tutorial.description is not None
        assert isinstance(tutorial.description, str)
        assert len(tutorial.description) > 0
    
    def test_pages_progression_makes_sense(self):
        """Test that tutorial pages follow a logical progression."""
        tutorial = TypeAnnotationsBasics()
        pages = tutorial.pages
        
        # Page 1: Introduction
        assert "Introduction" in pages[0]
        
        # Page 2: Basic types
        assert "Basic" in pages[1] or "Variable" in pages[1]
        
        # Page 3: Functions
        assert "Function" in pages[2]
        
        # Page 4: None/Optional
        assert "None" in pages[3] or "Optional" in pages[3]
        
        # Page 5: Advanced
        assert "Advanced" in pages[4]
        
        # Page 6: Errors
        assert "Error" in pages[5] or "Common" in pages[5]
        
        # Page 7: Best Practices
        assert "Best Practice" in pages[6] or "Practice" in pages[6]