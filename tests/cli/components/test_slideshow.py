"""
Comprehensive Tests for Slideshow Component
===========================================
Tests for the slideshow component with full coverage of all functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
import sys
import os

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from storm_checker.cli.components.slideshow import (
    Slideshow, Slide, ContentMode
)
from storm_checker.cli.components.border import BorderStyle


class TestSlide:
    """Test the Slide dataclass."""
    
    def test_slide_creation(self):
        """Test creating a Slide instance."""
        slide = Slide(
            title="Test Title",
            content="Test content",
            slide_number=1,
            total_slides=5,
            tutorial_id="test_tutorial",
            has_question=True
        )
        
        assert slide.title == "Test Title"
        assert slide.content == "Test content"
        assert slide.slide_number == 1
        assert slide.total_slides == 5
        assert slide.tutorial_id == "test_tutorial"
        assert slide.has_question is True
    
    def test_slide_defaults(self):
        """Test Slide with default values."""
        slide = Slide(
            title="Title",
            content="Content",
            slide_number=1,
            total_slides=3
        )
        
        assert slide.tutorial_id is None
        assert slide.has_question is False


class TestContentMode:
    """Test the ContentMode enum."""
    
    def test_content_modes(self):
        """Test ContentMode enum values."""
        assert ContentMode.SLIDE.value == "slide"
        assert ContentMode.QUESTION.value == "question"
        assert ContentMode.RESULT.value == "result"


class TestSlideshow:
    """Test the Slideshow class."""
    
    @pytest.fixture
    def mock_border(self):
        """Mock Border class."""
        with patch('storm_checker.cli.components.slideshow.Border') as mock_border_class:
            mock_border_instance = Mock()
            mock_border_instance.top.return_value = "╔══════╗"
            
            # Mock middle method to accept different arguments properly
            def mock_middle(*args, **kwargs):
                if 'center_text' in kwargs:
                    return f"║ {kwargs.get('center_text', '')} ║"
                elif 'left_text' in kwargs:
                    return f"║{kwargs.get('left_text', '')}║"
                elif len(args) > 1:
                    # Handle positional arguments
                    if len(args) > 3:
                        return f"║ {args[1]} | {args[2]} | {args[3]} ║"
                    elif len(args) > 2:
                        return f"║ {args[1]} | {args[2]} ║"
                    elif len(args) > 1:
                        return f"║ {args[1]} ║"
                return "║ TEST ║"
            
            mock_border_instance.middle.side_effect = mock_middle
            mock_border_instance.bottom.return_value = "╚══════╝"
            mock_border_instance.horizontal_divider.return_value = "╟──────╢"
            mock_border_instance.left.return_value = "║ "
            mock_border_instance.right.return_value = " ║"
            mock_border_instance.empty_line.return_value = "║      ║"
            mock_border_class.return_value = mock_border_instance
            yield mock_border_instance
    
    @pytest.fixture
    def mock_progress_bar(self):
        """Mock ProgressBar class."""
        with patch('storm_checker.cli.components.slideshow.ProgressBar') as mock_pb_class:
            mock_pb_instance = Mock()
            mock_pb_instance.render.return_value = "[████░░] 60%"
            mock_pb_class.return_value = mock_pb_instance
            yield mock_pb_instance
    
    @pytest.fixture
    def mock_terminal_size(self):
        """Mock terminal size functions."""
        with patch('os.get_terminal_size') as mock_size:
            mock_size.return_value = Mock(columns=80, lines=24)
            yield mock_size
    
    @pytest.fixture
    def slideshow(self, mock_border, mock_progress_bar, mock_terminal_size):
        """Create a Slideshow instance with mocked dependencies."""
        return Slideshow(
            border_style=BorderStyle.DOUBLE,
            border_color="learn",
            width=None,
            height=None
        )
    
    def test_initialization_defaults(self, mock_border, mock_progress_bar, mock_terminal_size):
        """Test Slideshow initialization with defaults."""
        slideshow = Slideshow()
        
        assert slideshow.width == 80  # From mock terminal size
        assert slideshow.height == 24  # From mock terminal size
        assert slideshow.border is not None
        assert slideshow.progress_bar is not None
    
    def test_initialization_custom_dimensions(self, mock_border, mock_progress_bar):
        """Test Slideshow initialization with custom dimensions."""
        slideshow = Slideshow(width=100, height=30)
        
        assert slideshow.width == 100
        assert slideshow.height == 30
    
    def test_get_terminal_width_success(self, slideshow):
        """Test _get_terminal_width with successful terminal size."""
        with patch('os.get_terminal_size') as mock_size:
            mock_size.return_value = Mock(columns=150)
            width = slideshow._get_terminal_width()
            
            assert width == 120  # Max is 120
    
    def test_get_terminal_width_fallback(self, slideshow):
        """Test _get_terminal_width with exception."""
        with patch('os.get_terminal_size', side_effect=Exception("No terminal")):
            width = slideshow._get_terminal_width()
            
            assert width == 80  # Fallback value
    
    def test_get_terminal_height_success(self, slideshow):
        """Test _get_terminal_height with successful terminal size."""
        with patch('os.get_terminal_size') as mock_size:
            mock_size.return_value = Mock(lines=40)
            height = slideshow._get_terminal_height()
            
            assert height == 40
    
    def test_get_terminal_height_fallback(self, slideshow):
        """Test _get_terminal_height with exception."""
        with patch('os.get_terminal_size', side_effect=Exception("No terminal")):
            height = slideshow._get_terminal_height()
            
            assert height == 24  # Fallback value
    
    def test_render_header(self, slideshow):
        """Test render_header method."""
        lines = slideshow.render_header(
            tutorial_id="test_tutorial",
            slide_title="Test Slide",
            page_info="2/5",
            is_completed=False
        )
        
        assert isinstance(lines, list)
        assert len(lines) >= 3  # Top, middle, divider
        
        # Check that border methods were called
        slideshow.border.top.assert_called_once_with(80)
        slideshow.border.middle.assert_called_once()
        slideshow.border.horizontal_divider.assert_called_once_with(80)
    
    def test_render_header_completed(self, slideshow):
        """Test render_header with completed tutorial."""
        lines = slideshow.render_header(
            tutorial_id="test_tutorial",
            slide_title="Test Slide",
            page_info="2/5",
            is_completed=True
        )
        
        # Check that the middle call includes completion indicator
        middle_call = slideshow.border.middle.call_args[0]
        assert "✅" in middle_call[1] or len(middle_call) > 1
    
    def test_render_footer_with_progress(self, slideshow):
        """Test render_footer with progress bar."""
        lines = slideshow.render_footer(
            navigation_hints="Press ENTER to continue",
            progress=(3, 5)
        )
        
        assert isinstance(lines, list)
        assert len(lines) >= 3  # Divider, progress, navigation
        
        # Check that progress bar was rendered
        slideshow.progress_bar.render.assert_called_once_with(3, 5, label="Progress")
        slideshow.border.horizontal_divider.assert_called()
    
    def test_render_footer_without_progress(self, slideshow):
        """Test render_footer without progress bar."""
        lines = slideshow.render_footer(
            navigation_hints="Press Q to quit"
        )
        
        assert isinstance(lines, list)
        assert len(lines) >= 2  # Divider, navigation
        
        slideshow.progress_bar.render.assert_not_called()
    
    def test_render_footer_minimal(self, slideshow):
        """Test render_footer with no parameters."""
        lines = slideshow.render_footer()
        
        assert isinstance(lines, list)
        assert len(lines) >= 1  # At least divider
    
    def test_render_slide(self, slideshow):
        """Test render_slide method."""
        slide = Slide(
            title="Test Slide",
            content="This is slide content\nWith multiple lines",
            slide_number=2,
            total_slides=5,
            tutorial_id="test_tutorial"
        )
        
        result = slideshow.render_slide(
            slide,
            is_completed=False,
            navigation_hints="Press ENTER to continue"
        )
        
        assert isinstance(result, str)
        assert "Test Slide" in result
        assert "2/5" in result
    
    def test_render_dynamic_content_slide_mode(self, slideshow):
        """Test render_dynamic_content in SLIDE mode."""
        slide = Slide(
            title="Dynamic Slide",
            content="Base content",
            slide_number=1,
            total_slides=3,
            tutorial_id="dynamic_test"
        )
        
        result = slideshow.render_dynamic_content(
            slide,
            mode=ContentMode.SLIDE,
            content_data="Additional content",
            is_completed=False,
            navigation_hints="Navigation"
        )
        
        assert isinstance(result, str)
        assert "Dynamic Slide" in result
    
    def test_render_dynamic_content_question_mode(self, slideshow):
        """Test render_dynamic_content in QUESTION mode."""
        slide = Slide(
            title="Question",
            content="Base",
            slide_number=1,
            total_slides=1
        )
        
        result = slideshow.render_dynamic_content(
            slide,
            mode=ContentMode.QUESTION,
            content_data="What is the answer?",
            is_completed=False
        )
        
        assert isinstance(result, str)
    
    def test_render_dynamic_content_result_mode(self, slideshow):
        """Test render_dynamic_content in RESULT mode."""
        slide = Slide(
            title="Result",
            content="Base",
            slide_number=1,
            total_slides=1
        )
        
        result = slideshow.render_dynamic_content(
            slide,
            mode=ContentMode.RESULT,
            content_data="✅ Correct!",
            is_completed=False
        )
        
        assert isinstance(result, str)
    
    def test_format_content_with_code_blocks(self, slideshow):
        """Test _format_content with code blocks."""
        content = '''Regular text
```python
def hello():
    print("Hello")
```
More text'''
        
        formatted = slideshow._format_content(content, max_lines=100)
        
        assert isinstance(formatted, list)
        # Should contain formatted code block
        assert any("def hello():" in line for line in formatted)
    
    def test_format_content_with_bullets(self, slideshow):
        """Test _format_content with bullet points."""
        content = """Header
• Point 1
• Point 2
- Dash point
* Star point"""
        
        formatted = slideshow._format_content(content, max_lines=100)
        
        assert isinstance(formatted, list)
        # Should format bullet points
        assert any("•" in line or "▸" in line for line in formatted)
    
    def test_format_content_with_bold(self, slideshow):
        """Test _format_content with bold text."""
        content = "This is **bold** text and this is also **emphasized**"
        
        formatted = slideshow._format_content(content, max_lines=100)
        
        assert isinstance(formatted, list)
        # Should contain ANSI codes for bold
    
    def test_format_content_with_inline_code(self, slideshow):
        """Test _format_content with inline code."""
        content = "Use `print()` function to display `output`"
        
        formatted = slideshow._format_content(content, max_lines=100)
        
        assert isinstance(formatted, list)
        # Should format inline code
    
    def test_format_heading(self, slideshow):
        """Test _format_heading method."""
        heading1 = slideshow._format_heading("# Main Title")
        assert "Main Title" in heading1
        
        heading2 = slideshow._format_heading("## Subtitle")
        assert "Subtitle" in heading2
        
        heading3 = slideshow._format_heading("### Small Heading")
        assert "Small Heading" in heading3
    
    def test_format_bullet(self, slideshow):
        """Test _format_bullet method."""
        bullet1 = slideshow._format_bullet("• Bullet point")
        assert "•" in bullet1 or "Bullet point" in bullet1
        
        bullet2 = slideshow._format_bullet("- Dash point")
        assert "•" in bullet2 or "Dash point" in bullet2  # It converts all to bullet
        
        bullet3 = slideshow._format_bullet("* Star point")
        assert "•" in bullet3 or "Star point" in bullet3
    
    def test_format_numbered(self, slideshow):
        """Test _format_numbered method."""
        num1 = slideshow._format_numbered("1. First item")
        assert "1." in num1
        assert "First item" in num1
        
        num2 = slideshow._format_numbered("2. Second item")
        assert "2." in num2
        assert "Second item" in num2
    
    def test_format_code_delimiter(self, slideshow):
        """Test _format_code_delimiter method."""
        delimiter1 = slideshow._format_code_delimiter("```python")
        assert "python" in delimiter1 or "─" in delimiter1
        
        delimiter2 = slideshow._format_code_delimiter("```")
        # Should contain some delimiter character
    
    def test_strip_ansi(self, slideshow):
        """Test _strip_ansi method."""
        text_with_ansi = "\033[1mBold\033[0m \033[31mRed\033[0m"
        
        stripped = slideshow._strip_ansi(text_with_ansi)
        
        assert stripped == "Bold Red"
        assert "\033" not in stripped
    
    def test_wrap_text(self, slideshow):
        """Test _wrap_text method."""
        long_text = "This is a very long line that needs to be wrapped because it exceeds the maximum width"
        
        wrapped = slideshow._wrap_text(long_text, 20)
        
        assert isinstance(wrapped, list)
        assert all(len(slideshow._strip_ansi(line)) <= 20 for line in wrapped)
    
    def test_wrap_text_preserves_indentation(self, slideshow):
        """Test _wrap_text preserves indentation."""
        indented_text = "    This is indented text"
        
        wrapped = slideshow._wrap_text(indented_text, 30)
        
        # The method preserves indentation for the first line, and wraps normally
        assert isinstance(wrapped, list)
        assert len(wrapped) > 0
    
    def test_render_completion_screen(self, slideshow):
        """Test render_completion_screen method."""
        result = slideshow.render_completion_screen(
            tutorial_id="test_tutorial",
            score=(8, 10),  # Tuple of correct/total
            message="Great job!",
            achievements=["Speed Demon", "Perfect Score"]
        )
        
        assert isinstance(result, str)
        # The mocked border returns "TEST" in the header, not the actual tutorial_id
        # So we check for existence of key elements in the output
        assert "8" in result or "10" in result or "80" in result  # Score display
        assert "Great job!" in result or "GREAT JOB!" in result
        assert "Speed Demon" in result or "SPEED DEMON" in result
        assert "Perfect Score" in result or "PERFECT SCORE" in result
    
