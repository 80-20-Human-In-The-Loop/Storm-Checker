import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

from logic.tutorial_engine import (
    TutorialData, TutorialEngine, TutorialState, TutorialProgress
)

@pytest.fixture
def sample_tutorial_data():
    return TutorialData(
        tutorial_id="test_tutorial",
        title="Test Tutorial",
        description="A tutorial for testing.",
        pages=[
            "# Introduction\nWelcome to the tutorial",
            "## Part 2\nMore content here",
            "Regular page without heading",
            "# Summary\nFinal page"
        ],
        questions={
            1: {"text": "Q1", "options": ["A", "B"], "correct_index": 0},
            3: {"text": "Final Q", "options": ["X", "Y"], "correct_index": 1}
        },
        difficulty=1,
        estimated_minutes=5,
        related_errors=["error1", "error2"]
    )

@pytest.fixture
def tutorial_engine(sample_tutorial_data):
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('logic.tutorial_engine.get_data_directory', return_value=Path(temp_dir)):
            return TutorialEngine(sample_tutorial_data)

def test_tutorial_engine_initialization(sample_tutorial_data):
    """Test that the TutorialEngine can be initialized."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('logic.tutorial_engine.get_data_directory', return_value=Path(temp_dir)):
            engine = TutorialEngine(sample_tutorial_data)
            assert isinstance(engine, TutorialEngine)
            assert engine.current_state == TutorialState.WELCOME
            assert engine.progress.current_page == 0
            assert engine.progress.pages_completed == 0

def test_load_progress_existing_file(sample_tutorial_data):
    """Test loading existing progress from file (lines 70-85)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create existing progress file
        progress_dir = Path(temp_dir) / "tutorial_progress"
        progress_dir.mkdir(exist_ok=True)
        progress_file = progress_dir / f"{sample_tutorial_data.tutorial_id}.json"
        
        existing_progress = {
            'tutorial_id': 'test_tutorial',
            'current_page': 2,
            'pages_completed': 2,
            'total_pages': 4,
            'questions_correct': 1,
            'total_questions': 2,
            'completed': True,
            'completion_time': '2023-01-01T12:00:00',
            'current_state': 'completion'
        }
        
        with open(progress_file, 'w') as f:
            json.dump(existing_progress, f)
        
        with patch('logic.tutorial_engine.get_data_directory', return_value=Path(temp_dir)):
            engine = TutorialEngine(sample_tutorial_data)
            
            # Should reset progress but keep completion status
            assert engine.progress.current_page == 0
            assert engine.progress.pages_completed == 0
            assert engine.progress.completed == True
            assert engine.progress.completion_time == '2023-01-01T12:00:00'

def test_load_progress_corrupted_file(sample_tutorial_data):
    """Test loading corrupted progress file (line 85)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create corrupted progress file
        progress_dir = Path(temp_dir) / "tutorial_progress"
        progress_dir.mkdir(exist_ok=True)
        progress_file = progress_dir / f"{sample_tutorial_data.tutorial_id}.json"
        
        with open(progress_file, 'w') as f:
            f.write("corrupted json data")
        
        with patch('logic.tutorial_engine.get_data_directory', return_value=Path(temp_dir)):
            engine = TutorialEngine(sample_tutorial_data)
            
            # Should create new progress
            assert engine.progress.current_page == 0
            assert engine.progress.completed == False

def test_save_progress(tutorial_engine):
    """Test save_progress method (lines 101-117)."""
    # Modify progress
    tutorial_engine.progress.current_page = 1
    tutorial_engine.progress.pages_completed = 1
    tutorial_engine.progress.questions_correct = 1
    
    # Mock file writing
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        tutorial_engine.save_progress()
    
    # Verify file was written
    mock_file.assert_called()
    written_data = ''.join(call.args[0] for call in mock_file().write.call_args_list)
    data = json.loads(written_data)
    
    assert data['tutorial_id'] == 'test_tutorial'
    assert data['current_page'] == 1
    assert data['pages_completed'] == 1
    assert data['questions_correct'] == 1

def test_can_resume(tutorial_engine):
    """Test can_resume method (line 121)."""
    # Initially cannot resume
    assert tutorial_engine.can_resume() == False
    
    # Can resume after progress
    tutorial_engine.progress.pages_completed = 1
    assert tutorial_engine.can_resume() == True
    
    # Cannot resume if completed
    tutorial_engine.progress.completed = True
    assert tutorial_engine.can_resume() == False

def test_resume_from_saved(tutorial_engine):
    """Test resume_from_saved method (line 125)."""
    tutorial_engine.progress.pages_completed = 2
    tutorial_engine.resume_from_saved()
    assert tutorial_engine.progress.current_page == 2

def test_get_current_page_data(tutorial_engine):
    """Test get_current_page_data method."""
    # First page
    data = tutorial_engine.get_current_page_data()
    assert data['page_number'] == 0
    assert data['slide_number'] == 1
    assert data['total_slides'] == 4
    assert data['title'] == "Introduction"
    assert "Welcome to the tutorial" in data['content']
    assert data['has_question'] == False
    
    # Page with question
    tutorial_engine.progress.current_page = 1
    data = tutorial_engine.get_current_page_data()
    assert data['has_question'] == True
    assert data['question']['text'] == "Q1"
    
    # Beyond last page (line 130)
    tutorial_engine.progress.current_page = 10
    assert tutorial_engine.get_current_page_data() is None

def test_extract_page_title(tutorial_engine):
    """Test _extract_page_title method including fallbacks."""
    # H1 heading
    assert tutorial_engine._extract_page_title(0) == "Introduction"
    
    # H2 heading
    assert tutorial_engine._extract_page_title(1) == "Part 2"
    
    # No heading - middle page
    assert tutorial_engine._extract_page_title(2) == "Part 3"
    
    # Last page with heading
    assert tutorial_engine._extract_page_title(3) == "Summary"
    
    # Test fallback for first page without heading (line 157)
    tutorial_engine.tutorial_data.pages[0] = "No heading here"
    assert tutorial_engine._extract_page_title(0) == "Introduction"
    
    # Test fallback for last page without heading
    tutorial_engine.tutorial_data.pages[3] = "No heading here"
    assert tutorial_engine._extract_page_title(3) == "Summary"

def test_navigation_methods(tutorial_engine):
    """Test navigation methods."""
    # can_go_next
    assert tutorial_engine.can_go_next() == True
    tutorial_engine.progress.current_page = 3
    assert tutorial_engine.can_go_next() == False
    
    # can_go_back
    tutorial_engine.progress.current_page = 0
    assert tutorial_engine.can_go_back() == False
    tutorial_engine.progress.current_page = 1
    assert tutorial_engine.can_go_back() == True
    
    # go_next
    tutorial_engine.progress.current_page = 0
    assert tutorial_engine.go_next() == True
    assert tutorial_engine.progress.current_page == 1
    assert tutorial_engine.progress.pages_completed == 1
    assert tutorial_engine.current_state == TutorialState.SLIDE_CONTENT
    
    # Cannot go next from last page
    tutorial_engine.progress.current_page = 3
    assert tutorial_engine.go_next() == False
    
    # go_back
    tutorial_engine.progress.current_page = 2
    assert tutorial_engine.go_back() == True
    assert tutorial_engine.progress.current_page == 1
    assert tutorial_engine.current_state == TutorialState.SLIDE_CONTENT
    
    # Cannot go back from first page
    tutorial_engine.progress.current_page = 0
    assert tutorial_engine.go_back() == False

def test_question_handling(tutorial_engine):
    """Test question-related methods."""
    # start_question
    tutorial_engine.start_question()
    assert tutorial_engine.current_state == TutorialState.QUESTION_ACTIVE
    
    # complete_question - correct answer
    result = tutorial_engine.complete_question(True)
    assert result == True
    assert tutorial_engine.progress.questions_correct == 1
    assert tutorial_engine.current_state == TutorialState.QUESTION_RESULT
    
    # complete_question - wrong answer on mid-tutorial question
    tutorial_engine.progress.current_page = 1
    tutorial_engine.current_state = TutorialState.QUESTION_ACTIVE
    result = tutorial_engine.complete_question(False)
    assert result == False
    assert tutorial_engine.current_state == TutorialState.FAILED
    
    # complete_question - wrong answer on final question
    tutorial_engine.progress.current_page = 3
    tutorial_engine.current_state = TutorialState.QUESTION_ACTIVE
    result = tutorial_engine.complete_question(False)
    assert result == True
    assert tutorial_engine.current_state == TutorialState.QUESTION_RESULT

def test_is_tutorial_complete(tutorial_engine):
    """Test is_tutorial_complete method."""
    assert tutorial_engine.is_tutorial_complete() == False
    
    tutorial_engine.progress.current_page = 3
    assert tutorial_engine.is_tutorial_complete() == True
    
    tutorial_engine.progress.current_page = 10
    assert tutorial_engine.is_tutorial_complete() == True

def test_complete_tutorial(tutorial_engine):
    """Test complete_tutorial method."""
    # Mock save_progress
    tutorial_engine.save_progress = MagicMock()
    
    # Mock ProgressTracker
    with patch('logic.progress_tracker.ProgressTracker') as MockTracker:
        mock_instance = MagicMock()
        MockTracker.return_value = mock_instance
        
        tutorial_engine.complete_tutorial()
        
        assert tutorial_engine.progress.completed == True
        assert tutorial_engine.progress.completion_time is not None
        assert tutorial_engine.current_state == TutorialState.COMPLETION
        tutorial_engine.save_progress.assert_called_once()
        mock_instance.update_tutorial_progress.assert_called_once_with('test_tutorial', 100.0)

def test_complete_tutorial_tracker_failure(tutorial_engine):
    """Test complete_tutorial when ProgressTracker fails."""
    # Mock save_progress
    tutorial_engine.save_progress = MagicMock()
    
    # Mock ProgressTracker to fail
    with patch('logic.progress_tracker.ProgressTracker', side_effect=Exception("Tracker error")):
        # Should not raise exception
        tutorial_engine.complete_tutorial()
        
        assert tutorial_engine.progress.completed == True
        assert tutorial_engine.current_state == TutorialState.COMPLETION

def test_get_completion_data(tutorial_engine):
    """Test get_completion_data method."""
    tutorial_engine.progress.questions_correct = 1
    tutorial_engine.progress.total_questions = 2
    
    data = tutorial_engine.get_completion_data()
    
    assert data['tutorial_id'] == 'test_tutorial'
    assert data['title'] == 'Test Tutorial'
    assert data['score'] == (1, 2)
    assert data['score_percentage'] == 50.0
    assert data['related_errors'] == ['error1', 'error2']
    
    # Test with no questions
    tutorial_engine.progress.total_questions = 0
    data = tutorial_engine.get_completion_data()
    assert data['score_percentage'] == 0

def test_tutorial_state_enum():
    """Test TutorialState enum values."""
    assert TutorialState.WELCOME.value == "welcome"
    assert TutorialState.SLIDE_CONTENT.value == "slide_content"
    assert TutorialState.QUESTION_PROMPT.value == "question_prompt"
    assert TutorialState.QUESTION_ACTIVE.value == "question_active"
    assert TutorialState.QUESTION_RESULT.value == "question_result"
    assert TutorialState.COMPLETION.value == "completion"
    assert TutorialState.FAILED.value == "failed"

def test_tutorial_progress_dataclass():
    """Test TutorialProgress dataclass."""
    progress = TutorialProgress(
        tutorial_id="test",
        current_page=0,
        pages_completed=0,
        total_pages=5,
        questions_correct=0,
        total_questions=2,
        completed=False
    )
    assert progress.tutorial_id == "test"
    assert progress.completion_time is None
    assert progress.current_state == TutorialState.WELCOME
