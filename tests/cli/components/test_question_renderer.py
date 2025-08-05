import pytest
from storm_checker.cli.components.question_renderer import QuestionRenderer
from storm_checker.cli.colors import THEME, RESET, BOLD

def test_question_renderer_initialization():
    """Test that the QuestionRenderer can be initialized."""
    try:
        renderer = QuestionRenderer()
        assert isinstance(renderer, QuestionRenderer)
    except Exception as e:
        pytest.fail(f"QuestionRenderer initialization failed with an exception: {e}")


class TestQuestionRenderer:
    """Test QuestionRenderer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = QuestionRenderer()
        
        # Sample question data for testing
        self.sample_question = {
            'question_text': 'What is the correct type annotation?',
            'options': ['str', 'int', 'float', 'bool'],
            'correct_index': 0,
            'selected_index': 1,
            'is_answered': False,
            'hint': 'Think about text data'
        }
    
    def test_format_question_text(self):
        """Test formatting of question text."""
        result = self.renderer.format_question_text(self.sample_question)
        
        assert self.sample_question['question_text'] in result
        assert "📚" in result
        assert str(THEME['learn']) in result
        assert BOLD in result
        assert RESET in result
    
    def test_format_hint_with_hint_unanswered(self):
        """Test formatting hint when hint exists and question is unanswered."""
        result = self.renderer.format_hint(self.sample_question)
        
        assert self.sample_question['hint'] in result
        assert "💡 Hint:" in result
        assert str(THEME['warning']) in result
        assert RESET in result
    
    def test_format_hint_with_hint_answered(self):
        """Test formatting hint when hint exists but question is answered."""
        answered_question = self.sample_question.copy()
        answered_question['is_answered'] = True
        
        result = self.renderer.format_hint(answered_question)
        assert result == ""
    
    def test_format_hint_no_hint(self):
        """Test formatting hint when no hint exists."""
        no_hint_question = self.sample_question.copy()
        del no_hint_question['hint']
        
        result = self.renderer.format_hint(no_hint_question)
        assert result == ""
    
    def test_format_options_unanswered(self):
        """Test formatting options when question is unanswered."""
        result = self.renderer.format_options(self.sample_question)
        
        assert len(result) == 4
        
        # Check selected option formatting
        assert "▶ 2. int" in result[1]  # selected_index = 1
        assert str(THEME['info']) in result[1]
        assert BOLD in result[1]
        
        # Check unselected option formatting
        assert "  1. str" in result[0]
        assert "  3. float" in result[2]
        assert "  4. bool" in result[3]
    
    def test_format_options_answered_correct(self):
        """Test formatting options when question is answered correctly."""
        answered_question = self.sample_question.copy()
        answered_question['is_answered'] = True
        answered_question['user_answer'] = 0  # Correct answer
        
        result = self.renderer.format_options(answered_question)
        
        # Check correct answer has checkmark
        assert "✓" in result[0]
        assert str(THEME['success']) in result[0]
    
    def test_format_options_answered_incorrect(self):
        """Test formatting options when question is answered incorrectly."""
        answered_question = self.sample_question.copy()
        answered_question['is_answered'] = True
        answered_question['user_answer'] = 1  # Incorrect answer
        
        result = self.renderer.format_options(answered_question)
        
        # Check correct answer has checkmark
        assert "✓" in result[0]
        assert str(THEME['success']) in result[0]
        
        # Check incorrect user answer has X
        assert "✗" in result[1]
        assert str(THEME['error']) in result[1]
        
        # Check other options have no symbols
        assert "✓" not in result[2] and "✗" not in result[2]
        assert "✓" not in result[3] and "✗" not in result[3]
    
    def test_format_complete_question_unanswered(self):
        """Test formatting complete question when unanswered."""
        result = self.renderer.format_complete_question(self.sample_question)
        
        # Should contain question text
        assert self.sample_question['question_text'] in result
        
        # Should contain hint
        assert self.sample_question['hint'] in result
        
        # Should contain all options
        for option in self.sample_question['options']:
            assert option in result
        
        # Should have proper structure (newlines)
        lines = result.split('\n')
        assert len(lines) >= 6  # question + hint + empty + 4 options
    
    def test_format_complete_question_no_hint(self):
        """Test formatting complete question without hint."""
        no_hint_question = self.sample_question.copy()
        del no_hint_question['hint']
        
        result = self.renderer.format_complete_question(no_hint_question)
        
        # Should contain question text
        assert no_hint_question['question_text'] in result
        
        # Should not contain hint indicator
        assert "💡 Hint:" not in result
        
        # Should contain all options
        for option in no_hint_question['options']:
            assert option in result
    
    def test_format_navigation_help(self):
        """Test formatting navigation help text."""
        result = self.renderer.format_navigation_help()
        
        assert "↑↓" in result
        assert "1-9" in result
        assert "Enter" in result
        assert str(THEME['text_muted']) in result
        assert RESET in result
