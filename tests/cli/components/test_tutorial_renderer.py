"""
Comprehensive Tests for TutorialRenderer
========================================
Tests for storm_checker/cli/components/tutorial_renderer.py with full coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from storm_checker.cli.components.tutorial_renderer import TutorialRenderer


class TestTutorialRenderer:
    """Test the TutorialRenderer class comprehensively."""
    
    def test_initialization_default(self):
        """Test TutorialRenderer initialization with defaults."""
        renderer = TutorialRenderer()
        assert isinstance(renderer, TutorialRenderer)
        assert renderer.width == 120
        assert renderer.border is not None
        assert renderer.progress_bar is not None
    
    def test_initialization_with_width(self):
        """Test TutorialRenderer initialization with custom width."""
        renderer = TutorialRenderer(width=100)
        # Width is fixed at 120 regardless of input
        assert renderer.width == 120
    
    @patch('os.get_terminal_size')
    def test_get_terminal_width_success(self, mock_terminal_size):
        """Test getting terminal width successfully."""
        mock_terminal_size.return_value = Mock(columns=150)
        renderer = TutorialRenderer()
        width = renderer._get_terminal_width()
        assert width == 120  # Capped at 120
        
        mock_terminal_size.return_value = Mock(columns=80)
        width = renderer._get_terminal_width()
        assert width == 80  # Below cap
    
    @patch('os.get_terminal_size', side_effect=Exception("No terminal"))
    def test_get_terminal_width_fallback(self, mock_terminal_size):
        """Test terminal width fallback on error."""
        renderer = TutorialRenderer()
        width = renderer._get_terminal_width()
        assert width == 80  # Fallback value
    
    def test_render_welcome_screen(self):
        """Test rendering welcome screen."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'title': 'Test Tutorial',
            'description': 'Learn about testing',
            'tutorial_id': 'test_tutorial'
        }
        
        result = renderer.render_welcome_screen(tutorial_data)
        
        assert 'Welcome to: Test Tutorial' in result
        assert 'Learn about testing' in result
        assert 'Press Enter to begin...' in result
    
    def test_render_slide_content_basic(self):
        """Test rendering basic slide content."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial',
            'completed': False
        }
        page_data = {
            'title': 'Page Title',
            'content': '# Heading\n\nSome content here.',
            'slide_number': 1,
            'total_slides': 3,
            'has_question': False
        }
        
        result = renderer.render_slide_content(tutorial_data, page_data)
        
        assert 'TUTORIAL: test_tutorial' in result
        assert 'Page Title' in result
        assert 'Page 1/3' in result
        assert 'Heading' in result
        assert 'Some content here.' in result
    
    def test_render_slide_content_with_question_prompt(self):
        """Test rendering slide with question prompt."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial',
            'completed': False
        }
        page_data = {
            'title': 'Page with Question',
            'content': 'Content before question.',
            'slide_number': 2,
            'total_slides': 3,
            'has_question': True
        }
        
        result = renderer.render_slide_content(tutorial_data, page_data, show_question_prompt=True)
        
        assert 'Press Enter for Knowledge Check' in result
        assert 'Content before question.' in result
    
    def test_render_slide_content_completed_tutorial(self):
        """Test rendering slide for completed tutorial."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial',
            'completed': True
        }
        page_data = {
            'title': 'Review Page',
            'content': 'Review content',
            'slide_number': 1,
            'total_slides': 1,
            'has_question': False
        }
        
        result = renderer.render_slide_content(tutorial_data, page_data)
        
        assert '✅' in result  # Completed indicator
        assert 'TUTORIAL: test_tutorial' in result
    
    def test_render_question_screen(self):
        """Test rendering question screen."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial',
            'completed': False
        }
        page_data = {
            'title': 'Question Page',
            'slide_number': 2,
            'total_slides': 3
        }
        question_content = "What is the answer to life?\nA) 42\nB) 24\nC) Unknown"
        
        result = renderer.render_question_screen(tutorial_data, page_data, question_content)
        
        assert 'Knowledge Check!' in result
        assert 'What is the answer to life?' in result
        assert 'A) 42' in result
        assert 'Answer the question to continue...' in result
    
    def test_render_question_screen_no_content(self):
        """Test rendering question screen without content."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial'
        }
        page_data = {
            'title': 'Question',
            'slide_number': 1,
            'total_slides': 1
        }
        
        result = renderer.render_question_screen(tutorial_data, page_data, None)
        
        assert 'Knowledge Check!' in result
        assert 'Answer the question to continue...' in result
    
    def test_render_question_screen_long_lines(self):
        """Test rendering question screen with long lines that need wrapping."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial'
        }
        page_data = {
            'title': 'Question',
            'slide_number': 1,
            'total_slides': 1
        }
        # Create a very long line that will need wrapping
        long_line = "This is a very long question that will definitely exceed the maximum width allowed for a single line in the terminal and will need to be wrapped to multiple lines"
        question_content = f"{long_line}\n\nA) Short answer\nB) Another answer"
        
        result = renderer.render_question_screen(tutorial_data, page_data, question_content)
        
        assert 'Knowledge Check!' in result
        # The long line should be present but potentially wrapped
        assert 'very long question' in result
    
    def test_render_result_screen_correct(self):
        """Test rendering result screen for correct answer."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial'
        }
        page_data = {
            'title': 'Question Result',
            'slide_number': 2,
            'total_slides': 3
        }
        result_data = {
            'is_correct': True,
            'correct_option': 'A) 42',
            'explanation': 'The answer is from Hitchhiker\'s Guide to the Galaxy.'
        }
        
        result = renderer.render_result_screen(tutorial_data, page_data, result_data)
        
        assert '✅ Correct! Well done!' in result
        assert 'Hitchhiker\'s Guide to the Galaxy' in result
        assert 'Press Enter to continue...' in result
    
    def test_render_result_screen_incorrect(self):
        """Test rendering result screen for incorrect answer."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial'
        }
        page_data = {
            'title': 'Question Result',
            'slide_number': 2,
            'total_slides': 3
        }
        result_data = {
            'is_correct': False,
            'correct_option': 'A) 42',
            'explanation': 'The answer is from Hitchhiker\'s Guide to the Galaxy. This is a much longer explanation that will test the word wrapping functionality of the renderer.'
        }
        
        result = renderer.render_result_screen(tutorial_data, page_data, result_data)
        
        assert '❌ Not quite right.' in result
        assert 'The correct answer is: A) 42' in result
        assert 'Hitchhiker\'s Guide' in result
        assert 'Press Enter to continue...' in result
    
    def test_render_result_screen_no_explanation(self):
        """Test rendering result screen without explanation."""
        renderer = TutorialRenderer()
        tutorial_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial'
        }
        page_data = {
            'title': 'Result',
            'slide_number': 1,
            'total_slides': 1
        }
        result_data = {
            'is_correct': True,
            'correct_option': 'A) Yes'
        }
        
        result = renderer.render_result_screen(tutorial_data, page_data, result_data)
        
        assert '✅ Correct! Well done!' in result
        assert '📖 Explanation:' not in result
    
    def test_render_completion_screen_excellent(self):
        """Test rendering completion screen with excellent score."""
        renderer = TutorialRenderer()
        completion_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial',
            'score': (9, 10),
            'score_percentage': 90.0,
            'related_errors': ['error-code-1', 'error-code-2', 'error-code-3', 'error-code-4']
        }
        
        result = renderer.render_completion_screen(completion_data)
        
        assert '🎉 Tutorial Complete! 🎉' in result
        assert 'Score: 9/10 (90%)' in result
        assert 'Excellent work!' in result
        assert 'This tutorial helps with these MyPy errors:' in result
        assert 'error-code-1' in result
        assert 'error-code-3' in result
        assert 'error-code-4' not in result  # Only top 3 shown
    
    def test_render_completion_screen_good(self):
        """Test rendering completion screen with good score."""
        renderer = TutorialRenderer()
        completion_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial',
            'score': (7, 10),
            'score_percentage': 70.0
        }
        
        result = renderer.render_completion_screen(completion_data)
        
        assert 'Score: 7/10 (70%)' in result
        assert 'Good job! Consider reviewing' in result
    
    def test_render_completion_screen_needs_practice(self):
        """Test rendering completion screen with low score."""
        renderer = TutorialRenderer()
        completion_data = {
            'tutorial_id': 'test_tutorial',
            'title': 'Test Tutorial',
            'score': (4, 10),
            'score_percentage': 40.0
        }
        
        result = renderer.render_completion_screen(completion_data)
        
        assert 'Score: 4/10 (40%)' in result
        assert 'Keep practicing!' in result
        assert 'review this tutorial again' in result
    
    def test_format_content_headings(self):
        """Test formatting content with headings."""
        renderer = TutorialRenderer()
        content = "# Main Heading\n## Subheading\nRegular text"
        
        lines = renderer._format_content(content)
        
        # Check that headings are formatted (will have ANSI codes)
        assert any('Main Heading' in line for line in lines)
        assert any('Subheading' in line for line in lines)
        assert any('Regular text' in line for line in lines)
    
    def test_format_content_lists(self):
        """Test formatting content with lists."""
        renderer = TutorialRenderer()
        content = """• Bullet point 1
- Bullet point 2
1. Numbered item
2. Another numbered item"""
        
        lines = renderer._format_content(content)
        
        assert any('Bullet point 1' in line for line in lines)
        assert any('Bullet point 2' in line for line in lines)
        assert any('Numbered item' in line for line in lines)
    
    def test_format_content_code_block(self):
        """Test formatting content with code blocks."""
        renderer = TutorialRenderer()
        content = """Some text
```python
def hello():
    return "world"
```
More text"""
        
        lines = renderer._format_content(content)
        
        assert any('Some text' in line for line in lines)
        assert any('def hello():' in line for line in lines)
        assert any('return "world"' in line for line in lines)
        assert any('More text' in line for line in lines)
    
    @patch('rich.console.Console')
    @patch('rich.syntax.Syntax')
    def test_format_code_block_with_rich(self, mock_syntax_class, mock_console_class):
        """Test code block formatting with Rich library."""
        renderer = TutorialRenderer()
        
        # Setup mocks
        mock_console = Mock()
        mock_capture = Mock()
        mock_capture.get.return_value = "formatted code output"
        mock_console.capture.return_value.__enter__ = Mock(return_value=mock_capture)
        mock_console.capture.return_value.__exit__ = Mock(return_value=False)
        mock_console_class.return_value = mock_console
        
        code_lines = ['def test():', '    return True']
        result = renderer._format_code_block(code_lines, 'python')
        
        assert 'formatted code output' in result[0]
    
    def test_format_code_block_fallback_python(self):
        """Test code block formatting fallback for Python."""
        renderer = TutorialRenderer()
        
        # Force the fallback by making the import fail
        code_lines = ['def test():', '    return "hello"', '# Comment']
        
        # Patch the actual import location inside the method
        with patch.object(renderer, '_format_code_block_fallback') as mock_fallback:
            mock_fallback.return_value = ['[python]', 'def test():', '    return "hello"', '# Comment']
            
            # Force ImportError in try block
            with patch('builtins.__import__', side_effect=ImportError("No Rich")):
                result = renderer._format_code_block(code_lines, 'python')
            
            # Check fallback was called
            mock_fallback.assert_called_once_with(code_lines, 'python')
    
    def test_format_code_block_fallback_toml(self):
        """Test code block formatting fallback for TOML."""
        renderer = TutorialRenderer()
        
        # Call the fallback directly
        code_lines = ['[tool.mypy]', 'strict = true', 'warn_return_any = false']
        result = renderer._format_code_block_fallback(code_lines, 'toml')
        
        assert '[toml]' in result[0]
        assert any('[tool.mypy]' in line for line in result)
        assert any('strict' in line for line in result)
    
    def test_format_code_block_fallback_generic(self):
        """Test code block formatting fallback for generic language."""
        renderer = TutorialRenderer()
        
        # Call the fallback directly
        code_lines = ['Some generic', 'code content']
        result = renderer._format_code_block_fallback(code_lines, 'text')
        
        assert '[text]' in result[0]
        assert any('Some generic' in line for line in result)
    
    def test_process_inline_markdown(self):
        """Test processing inline markdown formatting."""
        renderer = TutorialRenderer()
        
        # Test bold
        result = renderer._process_inline_markdown('This is **bold** text')
        assert 'bold' in result
        assert '**' not in result or result.count('**') < 2
        
        # Test italic
        result = renderer._process_inline_markdown('This is *italic* text')
        assert 'italic' in result
        assert result.count('*') < 2
        
        # Test inline code
        result = renderer._process_inline_markdown('Use `print()` function')
        assert 'print()' in result
        assert '`' not in result
        
        # Test mixed
        result = renderer._process_inline_markdown('**Bold** and *italic* with `code`')
        assert 'Bold' in result
        assert 'italic' in result
        assert 'code' in result
    
    def test_get_navigation_hints(self):
        """Test navigation hints generation."""
        renderer = TutorialRenderer()
        
        # Without question
        hints = renderer._get_navigation_hints(has_question=False)
        assert 'Enter: Next' in hints
        assert 'b: Back' in hints
        assert 'q: Quit' in hints
        
        # With question
        hints = renderer._get_navigation_hints(has_question=True)
        assert 'Enter: Knowledge Check' in hints
        assert 'b: Back' in hints
        assert 'q: Quit' in hints
    
    def test_strip_ansi(self):
        """Test ANSI escape sequence stripping."""
        renderer = TutorialRenderer()
        
        # Test with ANSI codes
        text_with_ansi = '\x1b[31mRed text\x1b[0m'
        result = renderer._strip_ansi(text_with_ansi)
        assert result == 'Red text'
        
        # Test without ANSI codes
        plain_text = 'Plain text'
        result = renderer._strip_ansi(plain_text)
        assert result == 'Plain text'
    
    def test_wrap_text(self):
        """Test text wrapping functionality."""
        renderer = TutorialRenderer()
        
        # Test normal wrapping
        text = "This is a long line that needs to be wrapped because it exceeds the maximum width"
        lines = renderer._wrap_text(text, 30)
        assert len(lines) > 1
        assert all(len(renderer._strip_ansi(line)) <= 35 for line in lines)  # Some tolerance
        
        # Test single word too long
        text = "supercalifragilisticexpialidocious"
        lines = renderer._wrap_text(text, 10)
        assert len(lines) == 1
        assert lines[0] == text  # Word forced on single line
        
        # Test with ANSI codes
        text = "\x1b[31mRed\x1b[0m text that needs wrapping"
        lines = renderer._wrap_text(text, 15)
        assert len(lines) >= 1
        assert 'Red' in ''.join(lines)
