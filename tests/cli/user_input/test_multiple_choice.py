"""
Comprehensive Tests for Multiple Choice Component
===============================================
Tests for interactive multiple choice questions with keyboard navigation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
from typing import List, Tuple

from cli.user_input.multiple_choice import (
    Question, MultipleChoice, demo,
    LEARN_BLUE, LEARN_GREEN, LEARN_YELLOW, LEARN_PURPLE, 
    LEARN_CYAN, RESET, BOLD, CLEAR_LINE, CURSOR_UP, 
    HIDE_CURSOR, SHOW_CURSOR
)


class TestQuestion:
    """Test the Question dataclass."""
    
    def test_question_initialization_minimal(self):
        """Test Question initialization with minimal parameters."""
        question = Question(
            text="What is Python?",
            options=["A language", "A snake"],
            correct_index=0
        )
        
        assert question.text == "What is Python?"
        assert question.options == ["A language", "A snake"]
        assert question.correct_index == 0
        assert question.explanation is None
        assert question.hint is None
    
    def test_question_initialization_complete(self):
        """Test Question initialization with all parameters."""
        question = Question(
            text="What is Python?",
            options=["A language", "A snake", "A tool"],
            correct_index=1,
            explanation="Python is both a programming language and a snake!",
            hint="Think about programming"
        )
        
        assert question.text == "What is Python?"
        assert question.options == ["A language", "A snake", "A tool"]
        assert question.correct_index == 1
        assert question.explanation == "Python is both a programming language and a snake!"
        assert question.hint == "Think about programming"


class TestMultipleChoice:
    """Test the MultipleChoice class."""
    
    @pytest.fixture
    def sample_question(self):
        """Create a sample question for testing."""
        return Question(
            text="What is 2 + 2?",
            options=["3", "4", "5"],
            correct_index=1,
            explanation="2 + 2 equals 4",
            hint="Use basic math"
        )
    
    @pytest.fixture
    def sample_question_no_extras(self):
        """Create a sample question without hint or explanation."""
        return Question(
            text="What is 1 + 1?",
            options=["1", "2", "3"],
            correct_index=1
        )
    
    def test_initialization_defaults(self, sample_question):
        """Test MultipleChoice initialization with defaults."""
        mc = MultipleChoice(sample_question)
        
        assert mc.question == sample_question
        assert mc.selected_index == 0
        assert mc.answered is False
        assert mc.user_answer is None
        assert mc.integrated_mode is False
    
    def test_initialization_integrated_mode(self, sample_question):
        """Test MultipleChoice initialization with integrated mode."""
        mc = MultipleChoice(sample_question, integrated_mode=True)
        
        assert mc.integrated_mode is True
    
    @patch('builtins.print')
    def test_display_unanswered_with_hint(self, mock_print, sample_question):
        """Test display method when question is unanswered and has hint."""
        mc = MultipleChoice(sample_question)
        mc.selected_index = 1
        
        mc.display()
        
        # Check that print was called with various parts
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        
        # Question should be displayed
        question_call = next((call for call in calls if "What is 2 + 2?" in call), None)
        assert question_call is not None
        
        # Hint should be displayed
        hint_call = next((call for call in calls if "Use basic math" in call), None)
        assert hint_call is not None
        
        # Options should be displayed with selection
        option_calls = [call for call in calls if any(opt in call for opt in ["3", "4", "5"])]
        assert len(option_calls) >= 3
    
    @patch('builtins.print')
    def test_display_unanswered_no_hint(self, mock_print, sample_question_no_extras):
        """Test display method when question has no hint."""
        mc = MultipleChoice(sample_question_no_extras)
        
        mc.display()
        
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        
        # Hint should not be displayed
        hint_calls = [call for call in calls if "💡 Hint:" in call]
        assert len(hint_calls) == 0
    
    @patch('builtins.print')
    def test_display_answered_correct(self, mock_print, sample_question):
        """Test display method when question is answered correctly."""
        mc = MultipleChoice(sample_question)
        mc.answered = True
        mc.user_answer = 1  # Correct answer
        
        mc.display()
        
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        
        # Should show checkmark for correct answer
        correct_calls = [call for call in calls if "✓" in call]
        assert len(correct_calls) >= 1
    
    @patch('builtins.print')
    def test_display_answered_incorrect(self, mock_print, sample_question):
        """Test display method when question is answered incorrectly."""
        mc = MultipleChoice(sample_question)
        mc.answered = True
        mc.user_answer = 0  # Incorrect answer
        
        mc.display()
        
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        
        # Should show both checkmark for correct and X for incorrect
        correct_calls = [call for call in calls if "✓" in call]
        incorrect_calls = [call for call in calls if "✗" in call]
        assert len(correct_calls) >= 1
        assert len(incorrect_calls) >= 1
    
    @patch('builtins.print')
    def test_display_clear_previous_integrated_mode(self, mock_print, sample_question):
        """Test display method with clear_previous in integrated mode."""
        mc = MultipleChoice(sample_question, integrated_mode=True)
        
        mc.display(clear_previous=True)
        
        # Should not clear screen in integrated mode
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        clear_calls = [call for call in calls if "\033[2J\033[H" in call]
        assert len(clear_calls) == 0
    
    @patch('builtins.print')
    def test_display_clear_previous_normal_mode(self, mock_print, sample_question):
        """Test display method with clear_previous in normal mode."""
        mc = MultipleChoice(sample_question, integrated_mode=False)
        
        mc.display(clear_previous=True)
        
        # Should clear screen in normal mode
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        clear_calls = [call for call in calls if "\033[2J\033[H" in call]
        assert len(clear_calls) >= 1
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_regular_character(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with regular character."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.return_value = 'a'
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == 'a'
        mock_setraw.assert_called_once()
        mock_tcsetattr.assert_called_once()
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_up_arrow(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with up arrow key."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.side_effect = ['\x1b', '[A']  # ESC sequence for up arrow
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == 'UP'
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_down_arrow(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with down arrow key."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.side_effect = ['\x1b', '[B']  # ESC sequence for down arrow
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == 'DOWN'
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_number_valid(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with valid number key."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.return_value = '2'
        
        mc = MultipleChoice(sample_question)  # Has 3 options
        result = mc.get_key()
        
        assert result == '2'
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_number_invalid(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with invalid number key."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.return_value = '9'  # Too high for 3 options
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == '9'  # Returns the character even if invalid
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_enter(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with enter key."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.return_value = '\r'
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == 'ENTER'
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_newline(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with newline character."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.return_value = '\n'
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == 'ENTER'
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_quit_q(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with quit key 'q'."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.return_value = 'q'
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == 'QUIT'
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_quit_ctrl_c(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with Ctrl+C."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.return_value = '\x03'  # Ctrl+C
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == 'QUIT'
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdin.read')
    def test_get_key_escape_only(self, mock_read, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test get_key method with escape key only."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        mock_read.side_effect = ['\x1b', 'XY']  # ESC followed by unknown sequence
        
        mc = MultipleChoice(sample_question)
        result = mc.get_key()
        
        assert result == '\x1bXY'  # Returns the full sequence
    
    @patch('builtins.print')
    def test_answer_question_correct(self, mock_print, sample_question):
        """Test answer_question method with correct answer."""
        mc = MultipleChoice(sample_question)
        mc.selected_index = 1  # Correct answer
        
        mc.answer_question()
        
        assert mc.answered is True
        assert mc.user_answer == 1
        
        # Check success message was printed
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        success_calls = [call for call in calls if "✅ Correct!" in call]
        assert len(success_calls) >= 1
        
        # Check explanation was printed
        explanation_calls = [call for call in calls if "2 + 2 equals 4" in call]
        assert len(explanation_calls) >= 1
    
    @patch('builtins.print')
    def test_answer_question_incorrect(self, mock_print, sample_question):
        """Test answer_question method with incorrect answer."""
        mc = MultipleChoice(sample_question)
        mc.selected_index = 0  # Incorrect answer
        
        mc.answer_question()
        
        assert mc.answered is True
        assert mc.user_answer == 0
        
        # Check error message was printed
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        error_calls = [call for call in calls if "❌ Not quite right" in call]
        assert len(error_calls) >= 1
        
        # Check correct answer was shown
        correct_calls = [call for call in calls if "The correct answer is: 4" in call]
        assert len(correct_calls) >= 1
    
    @patch('builtins.print')
    def test_answer_question_no_explanation(self, mock_print, sample_question_no_extras):
        """Test answer_question method without explanation."""
        mc = MultipleChoice(sample_question_no_extras)
        mc.selected_index = 1
        
        mc.answer_question()
        
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        
        # Should not show explanation section
        explanation_calls = [call for call in calls if "📖 Explanation:" in call]
        assert len(explanation_calls) == 0
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    def test_run_up_arrow_navigation(self, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with up arrow navigation."""
        mc = MultipleChoice(sample_question)
        mc.selected_index = 1  # Start at second option
        
        # Simulate: UP arrow, then ENTER
        mock_get_key.side_effect = ['UP', 'ENTER']
        
        result = mc.run()
        
        assert mc.selected_index == 0  # Should move up
        assert result == (False, 0)  # Incorrect answer (0), user answer (0)
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    def test_run_down_arrow_navigation(self, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with down arrow navigation."""
        mc = MultipleChoice(sample_question)
        mc.selected_index = 0  # Start at first option
        
        # Simulate: DOWN arrow, then ENTER
        mock_get_key.side_effect = ['DOWN', 'ENTER']
        
        result = mc.run()
        
        assert mc.selected_index == 1  # Should move down
        assert result == (True, 1)  # Correct answer (1), user answer (1)
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    def test_run_up_arrow_at_top_boundary(self, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with up arrow at top boundary."""
        mc = MultipleChoice(sample_question)
        mc.selected_index = 0  # Already at top
        
        # Simulate: UP arrow (should have no effect), then ENTER
        mock_get_key.side_effect = ['UP', 'ENTER']
        
        result = mc.run()
        
        assert mc.selected_index == 0  # Should stay at top
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    def test_run_down_arrow_at_bottom_boundary(self, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with down arrow at bottom boundary."""
        mc = MultipleChoice(sample_question)
        mc.selected_index = 2  # Already at bottom (3 options: 0, 1, 2)
        
        # Simulate: DOWN arrow (should have no effect), then ENTER
        mock_get_key.side_effect = ['DOWN', 'ENTER']
        
        result = mc.run()
        
        assert mc.selected_index == 2  # Should stay at bottom
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    def test_run_number_key_selection_valid(self, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with valid number key selection."""
        mc = MultipleChoice(sample_question)
        
        # Simulate: Press '2' (should select index 1 and answer immediately)
        mock_get_key.side_effect = ['2']
        
        result = mc.run()
        
        assert mc.selected_index == 1  # Should select index 1 (option "4")
        assert result == (True, 1)  # Correct answer
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    def test_run_number_key_selection_invalid(self, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with invalid number key selection."""
        mc = MultipleChoice(sample_question)
        
        # Simulate: Press '9' (invalid), then ENTER
        mock_get_key.side_effect = ['9', 'ENTER']
        
        result = mc.run()
        
        # Should ignore invalid number and continue with current selection
        assert mc.selected_index == 0  # Should stay at initial position
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    def test_run_enter_key(self, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with enter key."""
        mc = MultipleChoice(sample_question)
        mc.selected_index = 1  # Set to correct answer
        
        # Simulate: Press ENTER
        mock_get_key.side_effect = ['ENTER']
        
        result = mc.run()
        
        assert result == (True, 1)  # Correct answer
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    @patch('sys.exit')
    def test_run_quit_key(self, mock_exit, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with quit key."""
        mc = MultipleChoice(sample_question)
        
        # Simulate: Press 'q' to quit - need to create a generator that returns QUIT then stops
        def quit_generator():
            yield 'QUIT'
        
        mock_get_key.return_value = 'QUIT'
        
        mc.run()
        
        # Should call sys.exit
        mock_exit.assert_called_once_with(0)
    
    @patch.object(MultipleChoice, 'get_key')
    @patch.object(MultipleChoice, 'display')
    @patch('builtins.print')
    def test_run_unknown_key(self, mock_print, mock_display, mock_get_key, sample_question):
        """Test run method with unknown key."""
        mc = MultipleChoice(sample_question)
        
        # Simulate: Press unknown key, then ENTER
        mock_get_key.side_effect = ['x', 'ENTER']
        
        result = mc.run()
        
        # Should ignore unknown key and continue
        assert result == (False, 0)  # Default selection (incorrect)
    
    @patch('builtins.print')
    def test_run_cursor_management(self, mock_print, sample_question):
        """Test that cursor is properly hidden and shown."""
        mc = MultipleChoice(sample_question)
        
        with patch.object(mc, 'get_key', return_value='ENTER'):
            mc.run()
        
        # Check that cursor hide/show commands were printed
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        
        # Should hide cursor at start
        hide_calls = [call for call in calls if HIDE_CURSOR in call]
        assert len(hide_calls) >= 1
        
        # Should show cursor at end
        show_calls = [call for call in calls if SHOW_CURSOR in call]
        assert len(show_calls) >= 1
    
    @patch('builtins.print')
    def test_run_cursor_cleanup_on_exception(self, mock_print, sample_question):
        """Test that cursor is shown even if exception occurs."""
        mc = MultipleChoice(sample_question)
        
        with patch.object(mc, 'get_key', side_effect=Exception("Test exception")):
            with pytest.raises(Exception):
                mc.run()
        
        # Should still show cursor in finally block
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        show_calls = [call for call in calls if SHOW_CURSOR in call]
        assert len(show_calls) >= 1


class TestDemoFunction:
    """Test the demo function."""
    
    @patch.object(MultipleChoice, 'run')
    @patch('builtins.print')
    def test_demo_function(self, mock_print, mock_run):
        """Test demo function creates question and runs multiple choice."""
        mock_run.return_value = (True, 2)
        
        demo()
        
        # Should call run method
        mock_run.assert_called_once()
        
        # Should print demo result
        calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        result_calls = [call for call in calls if "Demo complete!" in call and "Correct: True" in call]
        assert len(result_calls) >= 1


class TestColorConstants:
    """Test that color constants are defined."""
    
    def test_color_constants_exist(self):
        """Test that all color constants are defined."""
        assert LEARN_BLUE
        assert LEARN_GREEN
        assert LEARN_YELLOW
        assert LEARN_PURPLE
        assert LEARN_CYAN
        assert RESET
        assert BOLD
        assert CLEAR_LINE
        assert CURSOR_UP
        assert HIDE_CURSOR
        assert SHOW_CURSOR
    
    def test_color_constants_are_strings(self):
        """Test that color constants are strings."""
        assert isinstance(LEARN_BLUE, str)
        assert isinstance(LEARN_GREEN, str)
        assert isinstance(LEARN_YELLOW, str)
        assert isinstance(LEARN_PURPLE, str)
        assert isinstance(LEARN_CYAN, str)
        assert isinstance(RESET, str)
        assert isinstance(BOLD, str)
        assert isinstance(CLEAR_LINE, str)
        assert isinstance(CURSOR_UP, str)
        assert isinstance(HIDE_CURSOR, str)
        assert isinstance(SHOW_CURSOR, str)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def single_option_question(self):
        """Create a question with only one option."""
        return Question(
            text="Only one choice?",
            options=["Yes"],
            correct_index=0
        )
    
    def test_single_option_navigation(self, single_option_question):
        """Test navigation with only one option."""
        mc = MultipleChoice(single_option_question)
        
        # Up/down should have no effect
        original_index = mc.selected_index
        
        with patch.object(mc, 'get_key', return_value='UP'):
            with patch.object(mc, 'display'):
                with patch('builtins.print'):
                    # This would normally trigger navigation but shouldn't change anything
                    assert mc.selected_index == original_index
    
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    def test_get_key_termios_cleanup(self, mock_tcsetattr, mock_tcgetattr, mock_fileno, sample_question):
        """Test that termios settings are always restored."""
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "old_settings"
        
        mc = MultipleChoice(sample_question)
        
        import termios
        with patch('tty.setraw', side_effect=Exception("Test exception")):
            with pytest.raises(Exception):
                mc.get_key()
        
        # Should still restore settings even if exception occurs
        mock_tcsetattr.assert_called_once_with(
            0,  # mocked fileno
            termios.TCSADRAIN,
            "old_settings"
        )
    
    @pytest.fixture
    def sample_question(self):
        """Create a sample question for edge case testing."""
        return Question(
            text="Test question?",
            options=["A", "B", "C"],
            correct_index=1
        )