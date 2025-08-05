"""
Comprehensive Tests for Base Tutorial Framework
==============================================
Tests for the BaseTutorial abstract class and TutorialProgress dataclass.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from typing import Dict, List

from storm_checker.tutorials.base_tutorial import (
    BaseTutorial, 
    TutorialProgress,
    THEME,
    RESET,
    BOLD,
    CLEAR_SCREEN,
    CURSOR_HIDE,
    CURSOR_SHOW
)
from storm_checker.cli.user_input.multiple_choice import Question


class ConcreteTutorial(BaseTutorial):
    """Concrete implementation of BaseTutorial for testing."""
    
    @property
    def title(self) -> str:
        return "Test Tutorial"
    
    @property
    def description(self) -> str:
        return "A test tutorial for unit testing"
    
    @property
    def pages(self) -> List[str]:
        return [
            "# Page 1\nThis is the first page",
            "# Page 2\nThis is the second page",
            "# Page 3\nThis is the third page"
        ]
    
    @property
    def questions(self) -> Dict[int, Question]:
        return {
            1: Question(
                text="What is 2+2?",
                options=["3", "4", "5"],
                correct_index=1,
                explanation="2+2 equals 4",
                hint="Think basic math"
            )
        }
    
    @property
    def related_errors(self) -> List[str]:
        return ["test-error", "another-error"]
    
    @property 
    def difficulty(self) -> int:
        return 2
    
    @property
    def estimated_minutes(self) -> int:
        return 15


class TestTutorialProgress:
    """Test the TutorialProgress dataclass."""
    
    def test_tutorial_progress_creation(self):
        """Test creating a TutorialProgress instance."""
        progress = TutorialProgress(
            tutorial_id="test_tutorial",
            pages_completed=2,
            total_pages=5,
            questions_correct=1,
            total_questions=2,
            completed=False,
            completion_time="2024-01-01T10:00:00"
        )
        
        assert progress.tutorial_id == "test_tutorial"
        assert progress.pages_completed == 2
        assert progress.total_pages == 5
        assert progress.questions_correct == 1
        assert progress.total_questions == 2
        assert progress.completed == False
        assert progress.completion_time == "2024-01-01T10:00:00"
    
    def test_tutorial_progress_to_dict(self):
        """Test converting TutorialProgress to dictionary."""
        progress = TutorialProgress(
            tutorial_id="test_tutorial",
            pages_completed=3,
            total_pages=5,
            questions_correct=2,
            total_questions=3,
            completed=True,
            completion_time="2024-01-01T15:30:00"
        )
        
        result = progress.to_dict()
        expected = {
            "tutorial_id": "test_tutorial",
            "pages_completed": 3,
            "total_pages": 5,
            "questions_correct": 2,
            "total_questions": 3,
            "completed": True,
            "completion_time": "2024-01-01T15:30:00"
        }
        
        assert result == expected
    
    def test_tutorial_progress_default_completion_time(self):
        """Test TutorialProgress with default completion_time (None)."""
        progress = TutorialProgress(
            tutorial_id="test",
            pages_completed=0,
            total_pages=3,
            questions_correct=0,
            total_questions=1,
            completed=False
        )
        
        assert progress.completion_time is None
        
        result = progress.to_dict()
        assert result["completion_time"] is None


class TestBaseTutorial:
    """Test the BaseTutorial abstract base class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_tutorial(self, temp_dir):
        """Create a concrete tutorial instance with mocked directories."""
        with patch('storm_checker.tutorials.base_tutorial.get_data_directory', return_value=temp_dir):
            with patch('storm_checker.tutorials.base_tutorial.ensure_directory', return_value=temp_dir / "tutorial_progress"):
                tutorial = ConcreteTutorial()
                yield tutorial
    
    def test_tutorial_initialization(self, mock_tutorial):
        """Test tutorial initialization."""
        assert mock_tutorial.tutorial_id == "concrete"  # ConcreteTutorial -> concrete
        assert mock_tutorial.current_page == 0
        assert isinstance(mock_tutorial.progress, TutorialProgress)
        assert mock_tutorial.progress.tutorial_id == "concrete"
    
    def test_abstract_properties_implemented(self, mock_tutorial):
        """Test that all abstract properties are properly implemented."""
        assert mock_tutorial.title == "Test Tutorial"
        assert mock_tutorial.description == "A test tutorial for unit testing"
        assert len(mock_tutorial.pages) == 3
        assert len(mock_tutorial.questions) == 1
        assert mock_tutorial.related_errors == ["test-error", "another-error"]
        assert mock_tutorial.difficulty == 2
        assert mock_tutorial.estimated_minutes == 15
    
    def test_default_properties(self):
        """Test default property implementations in base class."""
        class MinimalTutorial(BaseTutorial):
            @property
            def title(self):
                return "Minimal"
            
            @property
            def description(self):
                return "Minimal tutorial"
            
            @property
            def pages(self):
                return ["Page 1"]
            
            @property
            def questions(self):
                return {}
        
        with patch('storm_checker.tutorials.base_tutorial.get_data_directory'):
            with patch('storm_checker.tutorials.base_tutorial.ensure_directory'):
                tutorial = MinimalTutorial()
                
                # Test default implementations
                assert tutorial.related_errors == []
                assert tutorial.difficulty == 1
                assert tutorial.estimated_minutes == 10
                assert tutorial.id == "minimal"  # MinimalTutorial -> minimal
    
    def test_id_property_generation(self):
        """Test automatic ID generation from class name."""
        class MyAwesomeTutorial(BaseTutorial):
            @property
            def title(self):
                return "Awesome"
            
            @property 
            def description(self):
                return "Awesome tutorial"
            
            @property
            def pages(self):
                return ["Page 1"]
            
            @property
            def questions(self):
                return {}
        
        with patch('storm_checker.tutorials.base_tutorial.get_data_directory'):
            with patch('storm_checker.tutorials.base_tutorial.ensure_directory'):
                tutorial = MyAwesomeTutorial()
                assert tutorial.id == "myawesome"  # MyAwesomeTutorial -> myawesome
    
    def test_load_progress_fresh_start(self, mock_tutorial, temp_dir):
        """Test loading progress when no saved progress exists."""
        # Ensure no progress file exists
        progress_file = temp_dir / "tutorial_progress" / "concrete.json"
        assert not progress_file.exists()
        
        progress = mock_tutorial.load_progress()
        
        assert progress.tutorial_id == "concrete"
        assert progress.pages_completed == 0
        assert progress.total_pages == 3
        assert progress.questions_correct == 0
        assert progress.total_questions == 1
        assert progress.completed == False
        assert progress.completion_time is None
    
    def test_load_progress_existing_file(self, mock_tutorial, temp_dir):
        """Test loading progress from existing file."""
        # Create progress directory and file
        progress_dir = temp_dir / "tutorial_progress"
        progress_dir.mkdir(exist_ok=True)
        progress_file = progress_dir / "concrete.json"
        
        # Write test progress data
        test_data = {
            "tutorial_id": "concrete",
            "pages_completed": 2,
            "total_pages": 3,
            "questions_correct": 1,
            "total_questions": 1,
            "completed": False,
            "completion_time": None
        }
        
        with open(progress_file, 'w') as f:
            json.dump(test_data, f)
        
        progress = mock_tutorial.load_progress()
        
        assert progress.tutorial_id == "concrete"
        assert progress.pages_completed == 2
        assert progress.total_pages == 3
        assert progress.questions_correct == 1
        assert progress.total_questions == 1
        assert progress.completed == False
    
    def test_load_progress_corrupted_file(self, mock_tutorial, temp_dir):
        """Test loading progress when file is corrupted."""
        # Create progress directory and corrupted file
        progress_dir = temp_dir / "tutorial_progress"
        progress_dir.mkdir(exist_ok=True)
        progress_file = progress_dir / "concrete.json"
        
        # Write corrupted JSON
        with open(progress_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should fall back to fresh progress
        progress = mock_tutorial.load_progress()
        
        assert progress.tutorial_id == "concrete"
        assert progress.pages_completed == 0
        assert progress.completed == False
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_progress_file_operations(self, mock_json_dump, mock_file, mock_tutorial):
        """Test save_progress file operations."""
        mock_tutorial.progress.pages_completed = 2
        mock_tutorial.progress.questions_correct = 1
        
        mock_tutorial.save_progress()
        
        # Verify file was opened for writing
        mock_file.assert_called_once()
        # Verify JSON was dumped
        mock_json_dump.assert_called_once()
        
        # Check the data that was saved
        call_args = mock_json_dump.call_args
        saved_data = call_args[0][0]  # First argument to json.dump
        
        assert saved_data["tutorial_id"] == "concrete"
        assert saved_data["pages_completed"] == 2
        assert saved_data["questions_correct"] == 1
    
    @patch('storm_checker.tutorials.base_tutorial.ProgressTracker')
    def test_save_progress_with_global_tracker(self, mock_progress_tracker_class, mock_tutorial):
        """Test save_progress updates global progress tracker."""
        mock_tracker = Mock()
        mock_progress_tracker_class.return_value = mock_tracker
        
        mock_tutorial.progress.pages_completed = 2
        mock_tutorial.progress.total_pages = 3
        
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                mock_tutorial.save_progress()
        
        # Verify global tracker was called
        mock_progress_tracker_class.assert_called_once()
        mock_tracker.update_tutorial_progress.assert_called_once_with(
            "concrete", 
            (2 / 3) * 100  # 66.67%
        )
    
    @patch('storm_checker.tutorials.base_tutorial.ProgressTracker')
    def test_save_progress_tracker_failure_graceful(self, mock_progress_tracker_class, mock_tutorial):
        """Test save_progress handles tracker failures gracefully."""
        mock_progress_tracker_class.side_effect = Exception("Tracker failed")
        
        # Should not raise exception even if tracker fails
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                mock_tutorial.save_progress()  # Should not raise
    
    @patch('builtins.print')
    def test_display_header(self, mock_print, mock_tutorial):
        """Test display_header method."""
        mock_tutorial.current_page = 1  # On page 2 of 3
        
        mock_tutorial.display_header()
        
        # Verify print was called multiple times
        assert mock_print.call_count >= 5
        
        # Check that key elements were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        
        # Should contain tutorial title and description
        title_found = any("Test Tutorial" in call for call in print_calls)
        desc_found = any("A test tutorial for unit testing" in call for call in print_calls)
        progress_found = any("Progress:" in call for call in print_calls)
        page_info_found = any("Page 2 of 3" in call for call in print_calls)
        
        assert title_found, "Tutorial title should be displayed"
        assert desc_found, "Tutorial description should be displayed"
        assert progress_found, "Progress bar should be displayed"
        assert page_info_found, "Page information should be displayed"
    
    def test_display_completion(self, mock_tutorial):
        """Test display_completion method."""
        mock_tutorial.progress.questions_correct = 1
        mock_tutorial.progress.total_questions = 1
        
        # Mock the slideshow to avoid the Border method issue
        with patch.object(mock_tutorial.slideshow, 'render_completion_screen', return_value="Completion Screen"):
            with patch('builtins.print') as mock_print:
                mock_tutorial.display_completion()
                
                # Verify print was called (completion screen was displayed)
                mock_print.assert_called()
                
                # Verify slideshow was called with correct parameters
                mock_tutorial.slideshow.render_completion_screen.assert_called_once()
    
    def test_display_page_valid_page(self, mock_tutorial):
        """Test display_page with valid page number."""
        # Mock the slideshow render_dynamic_content method and print
        with patch.object(mock_tutorial.slideshow, 'render_dynamic_content', return_value="Mock slide content") as mock_render:
            with patch('builtins.print') as mock_print:
                result = mock_tutorial.display_page(0)
                
                assert result == True
                mock_render.assert_called()
                mock_print.assert_called()
    
    def test_display_page_invalid_page(self, mock_tutorial):
        """Test display_page with invalid page number."""
        result = mock_tutorial.display_page(999)  # Beyond available pages
        assert result == True  # Should handle gracefully
    
    @patch('storm_checker.tutorials.base_tutorial.MultipleChoice')
    def test_display_page_with_question_enter_choice(self, mock_mc_class, mock_tutorial):
        """Test display_page with question when user presses Enter."""
        # Set up mock for MultipleChoice
        mock_mc = Mock()
        mock_mc.run.return_value = (True, 0)  # Correct answer
        mock_mc_class.return_value = mock_mc
        
        # Mock the slideshow and input methods
        with patch.object(mock_tutorial.slideshow, 'render_dynamic_content', return_value="Mock content"):
            with patch('builtins.print'):
                with patch('builtins.input', return_value=''):  # Simulate Enter key
                    with patch('builtins.input', return_value=''):  # For final input() wait
                        result = mock_tutorial.display_page(1)  # Page with question
                        
                        assert result == True
                        mock_mc.run.assert_called_once()
                        # Check that questions_correct was incremented
                        assert mock_tutorial.progress.questions_correct == 1
    
    def test_display_page_with_question_quit_choice(self, mock_tutorial):
        """Test display_page with question when user chooses to quit."""
        with patch.object(mock_tutorial.slideshow, 'render_dynamic_content', return_value="Mock content"):
            with patch('builtins.print'):
                with patch('builtins.input', return_value='q'):  # User quits
                    result = mock_tutorial.display_page(1)  # Page with question
                    
                    assert result == False  # Should return False for quit
    
    def test_display_page_with_question_back_choice(self, mock_tutorial):
        """Test display_page with question when user chooses to go back."""
        with patch.object(mock_tutorial.slideshow, 'render_dynamic_content', return_value="Mock content"):
            with patch('builtins.print'):
                with patch('builtins.input', return_value='b'):  # User goes back
                    result = mock_tutorial.display_page(1)  # Page with question
                    
                    assert result == True  # Should return True for back
    
    @patch('storm_checker.tutorials.base_tutorial.MultipleChoice')
    def test_display_page_with_question_incorrect_answer_mid_tutorial(self, mock_mc_class, mock_tutorial):
        """Test display_page with incorrect answer in middle of tutorial (should boot user)."""
        # Set up mock for MultipleChoice
        mock_mc = Mock()
        mock_mc.run.return_value = (False, 0)  # Incorrect answer
        mock_mc_class.return_value = mock_mc
        
        with patch.object(mock_tutorial.slideshow, 'render_dynamic_content', return_value="Mock content"):
            with patch('builtins.print'):
                with patch('builtins.input', return_value=''):  # Simulate Enter
                    with patch('builtins.input', return_value=''):  # For final input() wait
                        result = mock_tutorial.display_page(1)  # Page 1 (mid-tutorial)
                        
                        assert result == False  # Should boot user out
                        assert mock_tutorial.progress.questions_correct == 0  # No increment
    
    @patch('storm_checker.tutorials.base_tutorial.MultipleChoice')
    def test_display_page_with_question_incorrect_answer_final_page(self, mock_mc_class, mock_tutorial):
        """Test display_page with incorrect answer on final page (should not boot user)."""
        # Set up mock for MultipleChoice
        mock_mc = Mock()
        mock_mc.run.return_value = (False, 0)  # Incorrect answer
        mock_mc_class.return_value = mock_mc
        
        with patch.object(mock_tutorial.slideshow, 'render_dynamic_content', return_value="Mock content"):
            with patch('builtins.print'):
                with patch('builtins.input', return_value=''):  # Simulate Enter
                    with patch('builtins.input', return_value=''):  # For final input() wait
                        # Use final page (len(pages) - 1 = 2)
                        result = mock_tutorial.display_page(2)  # Final page
                        
                        assert result == True  # Should continue (not boot out on final page)
    
    def test_get_page_title_with_question(self, mock_tutorial):
        """Test _get_page_title when page has a question."""
        title = mock_tutorial._get_page_title(1)  # Page 1 has a question
        # The title should be extracted from the page content (# Page 2)
        assert title == "Page 2"
    
    def test_get_page_title_without_question(self, mock_tutorial):
        """Test _get_page_title when page has no question."""
        title = mock_tutorial._get_page_title(0)  # Page 0 has no question
        assert "Page 1" in title  # Should show page number
    
    def test_get_page_title_markdown_h2_heading(self, mock_tutorial):
        """Test _get_page_title with markdown h2 heading."""
        # Create a tutorial with h2 heading
        test_pages = ["## Advanced Concepts\nThis page has h2 heading"]
        with patch.object(type(mock_tutorial), 'pages', new_callable=lambda: property(lambda self: test_pages)):
            title = mock_tutorial._get_page_title(0)
            assert title == "Advanced Concepts"
    
    def test_get_page_title_no_heading_first_page(self, mock_tutorial):
        """Test _get_page_title with no heading on first page."""
        test_pages = ["This page has no heading"]
        with patch.object(type(mock_tutorial), 'pages', new_callable=lambda: property(lambda self: test_pages)):
            title = mock_tutorial._get_page_title(0)
            assert title == "Introduction"
    
    def test_get_page_title_no_heading_last_page(self, mock_tutorial):
        """Test _get_page_title with no heading on last page."""
        test_pages = ["Page 1", "Page 2", "This is the final page with no heading"]
        with patch.object(type(mock_tutorial), 'pages', new_callable=lambda: property(lambda self: test_pages)):
            title = mock_tutorial._get_page_title(2)  # Last page
            assert title == "Summary"
    
    def test_get_page_title_no_heading_middle_page(self, mock_tutorial):
        """Test _get_page_title with no heading on middle page."""
        test_pages = ["Page 1", "This middle page has no heading", "Page 3"]
        with patch.object(type(mock_tutorial), 'pages', new_callable=lambda: property(lambda self: test_pages)):
            title = mock_tutorial._get_page_title(1)  # Middle page (index 1)
            assert title == "Part 2"  # Should be page_number + 1
    
    def test_display_completion_score_variations(self, mock_tutorial):
        """Test display_completion with different score ranges."""
        test_cases = [
            (1, 1, 100, "Excellent work!"),  # 100% - excellent
            (4, 5, 80, "Excellent work!"),   # 80% - excellent
            (3, 5, 60, "Good job!"),         # 60% - good
            (2, 5, 40, "Keep practicing!"), # 40% - needs practice
        ]
        
        for correct, total, expected_pct, expected_message in test_cases:
            # Reset progress
            mock_tutorial.progress.questions_correct = correct
            mock_tutorial.progress.total_questions = total
            
            with patch.object(mock_tutorial.slideshow, 'render_completion_screen', return_value="Mock completion") as mock_render:
                with patch('builtins.print') as mock_print:
                    mock_tutorial.display_completion()
                    
                    # Verify the completion screen was rendered
                    mock_render.assert_called_once()
                    mock_print.assert_called_with("Mock completion")
                    
                    # Check the message passed to render_completion_screen
                    call_args = mock_render.call_args[0]  # positional args
                    message = call_args[2]  # Third argument is message
                    
                    assert f"{correct}/{total} ({expected_pct:.0f}%)" in message
                    assert expected_message in message
    
    def test_display_completion_with_related_errors(self, mock_tutorial):
        """Test display_completion includes related errors in message."""
        mock_tutorial.progress.questions_correct = 1
        mock_tutorial.progress.total_questions = 1
        
        with patch.object(mock_tutorial.slideshow, 'render_completion_screen', return_value="Mock completion") as mock_render:
            with patch('builtins.print'):
                mock_tutorial.display_completion()
                
                # Check that related errors are included in the message
                call_args = mock_render.call_args[0]
                message = call_args[2]  # Message is third argument
                
                assert "This tutorial helps with these MyPy errors:" in message
                assert "test-error" in message
                assert "another-error" in message
    
    @patch('storm_checker.cli.interactive.tutorial_controller.TutorialController')
    @patch('storm_checker.logic.tutorial_engine.TutorialData')
    @patch('storm_checker.logic.question_engine.Question')
    def test_run_method_execution(self, mock_question, mock_tutorial_data, mock_controller, mock_tutorial):
        """Test the run method creates proper objects and calls controller."""
        mock_controller_instance = Mock()
        mock_controller.return_value = mock_controller_instance
        
        mock_tutorial.run()
        
        # Verify TutorialController was instantiated and run was called
        mock_controller.assert_called_once()
        mock_controller_instance.run.assert_called_once()
    
    def test_get_tutorial_for_error_class_method(self):
        """Test the class method get_tutorial_for_error."""
        # This is a placeholder implementation in the base class
        result = BaseTutorial.get_tutorial_for_error("some-error")
        assert result is None  # Base implementation returns None
    
    @patch('builtins.print')
    def test_display_header_progress_calculation(self, mock_print, mock_tutorial):
        """Test progress bar calculation in display_header."""
        # Test different progress states
        test_cases = [
            (0, 3, 0),    # 0% progress
            (1, 3, 33),   # 33% progress  
            (2, 3, 67),   # 67% progress
            (3, 3, 100),  # 100% progress
        ]
        
        for current, total, expected_pct in test_cases:
            mock_tutorial.current_page = current
            mock_print.reset_mock()
            
            mock_tutorial.display_header()
            
            # Check that progress percentage is displayed correctly
            print_calls = [str(call) for call in mock_print.call_args_list]
            progress_call = next((call for call in print_calls if f"{expected_pct}%" in call), None)
            assert progress_call is not None, f"Expected {expected_pct}% progress not found"
    
    def test_tutorial_properties_consistency(self, mock_tutorial):
        """Test that tutorial properties are consistent."""
        # Verify pages and questions are consistent
        assert len(mock_tutorial.pages) > 0
        assert all(isinstance(page, str) for page in mock_tutorial.pages)
        
        # Verify question page numbers are valid
        for page_num in mock_tutorial.questions.keys():
            assert 0 <= page_num < len(mock_tutorial.pages)
        
        # Verify progress is initialized correctly
        assert mock_tutorial.progress.total_pages == len(mock_tutorial.pages)
        assert mock_tutorial.progress.total_questions == len(mock_tutorial.questions)
    
    def test_progress_directory_creation(self, temp_dir):
        """Test that progress directory is created properly."""
        with patch('storm_checker.tutorials.base_tutorial.get_data_directory', return_value=temp_dir):
            with patch('storm_checker.tutorials.base_tutorial.ensure_directory') as mock_ensure:
                mock_ensure.return_value = temp_dir / "tutorial_progress"
                
                ConcreteTutorial()
                
                # Verify ensure_directory was called with correct path
                mock_ensure.assert_called_once_with(temp_dir / "tutorial_progress")