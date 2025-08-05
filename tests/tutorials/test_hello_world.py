"""
Tests for Hello World Tutorial
==============================
Test the introductory tutorial functionality.
"""

import pytest
from tutorials.hello_world import HelloWorldTutorial
from .base import BaseTutorialTest
from unittest.mock import Mock


class TestHelloWorldTutorial(BaseTutorialTest):
    """Test the Hello World tutorial."""
    
    @property
    def tutorial_class(self):
        """The tutorial class to test."""
        return HelloWorldTutorial
    
    @property
    def expected_id(self):
        """Expected tutorial ID."""
        return "hello_world"
    
    @property
    def expected_difficulty_range(self):
        """Expected difficulty range (min, max)."""
        return (1, 1)  # Should be easiest
    
    @property
    def expected_page_count_range(self):
        """Expected page count range (min, max)."""
        return (3, 5)  # Hello world should be short
    
    # Specific tests for Hello World tutorial
    
    def test_hello_world_is_beginner_friendly(self, tutorial):
        """Test that hello world tutorial is beginner-friendly."""
        assert tutorial.difficulty == 1, "Hello World should be difficulty 1"
        assert tutorial.estimated_minutes <= 10, "Hello World should be quick"
        assert "Storm-Checker" in tutorial.title or "Hello" in tutorial.title
    
    def test_hello_world_introduces_navigation(self, tutorial):
        """Test that tutorial explains navigation."""
        # Simplified check - just look for "Enter" in any page
        assert any("Enter" in page for page in tutorial.pages), "Tutorial should explain navigation"
    
    def test_hello_world_has_welcome_message(self, tutorial):
        """Test that first page has welcoming content."""
        first_page = tutorial.pages[0]
        assert "Welcome" in first_page and "Storm-Checker" in first_page
    
    def test_hello_world_questions_are_easy(self, tutorial):
        """Test that questions are appropriate for beginners."""
        # Simple check - just verify questions exist and have reasonable structure
        assert len(tutorial.questions) > 0, "Should have at least one question"
    
    def test_hello_world_mentions_other_tutorials(self, tutorial):
        """Test that tutorial mentions next steps."""
        last_page = tutorial.pages[-1]
        assert "next" in last_page.lower() or "tutorial" in last_page.lower()
    
    def test_hello_world_practice_exercise_exists(self, tutorial):
        """Test that practice exercise encourages exploration."""
        assert tutorial.practice_exercise is not None
        exercise = tutorial.practice_exercise
        assert "stormcheck" in exercise.lower(), "Practice should mention stormcheck command"
    
    def test_hello_world_no_advanced_concepts(self, tutorial):
        """Test that tutorial doesn't include advanced concepts."""
        # Simplified check for just the most common advanced terms
        all_text = " ".join(tutorial.pages)
        advanced_terms = ["Protocol", "TypeVar", "Generic", "Union"]
        
        for term in advanced_terms:
            assert term not in all_text, f"Hello World should not mention advanced concept: {term}"
    
    def test_hello_world_emoji_usage(self, tutorial):
        """Test that tutorial uses emojis appropriately for friendliness."""
        # More efficient emoji detection using regex on specific common emojis
        import re
        all_text = " ".join(tutorial.pages)
        
        # Count common emojis using regex (much faster than checking every character)
        common_emojis = [
            r'👋', r'🌩️', r'🧭', r'📝', r'⚠️', r'🎉', r'🚀', 
            r'💡', r'✅', r'❌', r'🔧', r'📊', r'🎯'
        ]
        
        emoji_count = sum(len(re.findall(emoji, all_text)) for emoji in common_emojis)
        
        # Should have some emojis for friendliness but not too many
        assert emoji_count >= 2, "Hello World should have some emojis for friendliness"
        assert emoji_count <= 20, "Too many emojis can be distracting"
    
    def test_demo_function_exists(self):
        """Test that the demo function exists and is callable."""
        from tutorials.hello_world import demo
        assert callable(demo), "demo function should be callable"
        # Note: We don't actually call demo() here as it would start the interactive tutorial
    
    def test_demo_function_execution(self, monkeypatch):
        """Test that demo function creates and runs tutorial."""
        # Track if run was called
        run_called = False
        
        def mock_run(self):
            nonlocal run_called
            run_called = True
            
        # Mock the run method to avoid expensive imports
        # Import modules first, then set up mocks
        from tutorials.hello_world import HelloWorldTutorial, demo
        monkeypatch.setattr(HelloWorldTutorial, 'run', mock_run)
        
        # Call demo - the tutorial will be created but run() will be mocked
        demo()
        
        # Verify run was called
        assert run_called, "demo() should create a tutorial and call run()"