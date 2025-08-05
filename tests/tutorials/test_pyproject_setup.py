"""
Tests for Pyproject Setup Tutorial
==================================
Test the pyproject.toml configuration tutorial.
"""

import pytest
from tutorials.pyproject_setup import PyprojectSetupTutorial
from .base import BaseTutorialTest


class TestPyprojectSetupTutorial(BaseTutorialTest):
    """Test the pyproject.toml setup tutorial."""
    
    @property
    def tutorial_class(self):
        """The tutorial class to test."""
        return PyprojectSetupTutorial
    
    @property
    def expected_id(self):
        """Expected tutorial ID."""
        return "pyproject_setup"
    
    @property
    def expected_difficulty_range(self):
        """Expected difficulty range (min, max)."""
        return (1, 2)  # Configuration is basic
    
    @property
    def expected_page_count_range(self):
        """Expected page count range (min, max)."""
        return (4, 6)  # Need to cover various config options
    
    # Specific tests for pyproject setup tutorial
    
    def test_pyproject_covers_main_tables(self, tutorial):
        """Test that tutorial covers the main TOML tables."""
        all_text = " ".join(tutorial.pages)
        
        # Should mention all three main tables
        assert "[project]" in all_text, "Should cover [project] table"
        assert "[tool]" in all_text, "Should cover [tool] table"
        assert "[build-system]" in all_text, "Should cover [build-system] table"
        
        # Should specifically cover MyPy configuration
        assert "[tool.mypy]" in all_text, "Should cover [tool.mypy] specifically"
    
    def test_pyproject_includes_code_examples(self, tutorial):
        """Test that tutorial includes TOML code examples."""
        toml_blocks = 0
        for page in tutorial.pages:
            # Count TOML code blocks
            toml_blocks += page.count("```toml")
        
        assert toml_blocks >= 3, "Should have at least 3 TOML code examples"
    
    def test_pyproject_covers_essential_mypy_settings(self, tutorial):
        """Test that essential MyPy settings are covered."""
        essential_settings = [
            "python_version",
            "ignore_missing_imports",
            "show_error_codes",
            "check_untyped_defs",
            "disallow_untyped_defs"
        ]
        
        all_text = " ".join(tutorial.pages)
        for setting in essential_settings:
            assert setting in all_text, f"Should cover essential setting: {setting}"
    
    def test_pyproject_explains_strictness_levels(self, tutorial):
        """Test that tutorial explains gradual strictness."""
        all_text = " ".join(tutorial.pages).lower()
        
        # Should mention gradual adoption or starting lenient
        assert any(term in all_text for term in ["gradual", "lenient", "strict", "incremental"])
        assert "strict" in all_text, "Should discuss strictness levels"
    
    def test_pyproject_covers_per_module_config(self, tutorial):
        """Test that tutorial covers per-module configuration."""
        all_text = " ".join(tutorial.pages)
        
        assert "[[tool.mypy.overrides]]" in all_text, "Should cover overrides"
        assert "module =" in all_text, "Should show module-specific config"
    
    def test_pyproject_related_errors_accurate(self, tutorial):
        """Test that related errors are accurate."""
        assert "config-error" in tutorial.related_errors
        assert "import-untyped" in tutorial.related_errors
    
    def test_pyproject_questions_test_understanding(self, tutorial):
        """Test that questions cover key concepts."""
        # Collect all question topics
        question_texts = " ".join(q.text for q in tutorial.questions.values())
        
        # Should have questions about key concepts
        assert any(term in question_texts for term in ["PyPI", "name", "naming"])
        assert any(term in question_texts for term in ["strict", "lenient", "gradual"])
        assert "overrides" in question_texts.lower()
    
    def test_pyproject_explains_common_errors(self, tutorial):
        """Test that tutorial explains common configuration errors."""
        all_text = " ".join(tutorial.pages)
        
        # Should mention common issues
        assert any(term in all_text for term in ["Cannot find implementation", "missing stub", "import"])
        assert "ignore_missing_imports" in all_text
    
    def test_pyproject_naming_rules_explained(self, tutorial):
        """Test that project naming rules are explained."""
        naming_page_found = False
        for page in tutorial.pages:
            if "naming" in page.lower() and any(char in page for char in ["-", "_", "."]):
                naming_page_found = True
                break
        
        assert naming_page_found, "Should explain project naming rules"
    
    def test_pyproject_practice_exercise_actionable(self, tutorial):
        """Test that practice exercise is actionable."""
        assert tutorial.practice_exercise is not None
        exercise = tutorial.practice_exercise
        
        # Should guide user to create actual config
        assert "pyproject.toml" in exercise
        assert any(action in exercise.lower() for action in ["create", "add", "run"])
    
    def test_pyproject_migration_strategy_mentioned(self, tutorial):
        """Test that gradual migration strategy is mentioned."""
        strategy_found = False
        for page in tutorial.pages:
            if "migration" in page.lower() or "gradual" in page.lower():
                strategy_found = True
                break
        
        assert strategy_found, "Should mention migration/gradual adoption strategy"
    
    def test_pyproject_stormchecker_compatibility(self, tutorial):
        """Test that Storm Checker specific settings are mentioned."""
        all_text = " ".join(tutorial.pages)
        
        # Should mention pretty=false for stormchecker
        assert "pretty" in all_text
        assert "false" in all_text
        assert any(term in all_text.lower() for term in ["stormchecker", "storm-checker", "storm checker"])