"""
Comprehensive Tests for Progress Tracker
=======================================
Tests for progress tracking and achievement system with full coverage of all functionality.
"""

import json
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

from logic.progress_tracker import Achievement, SessionStats, ProgressData, ProgressTracker
from logic.mypy_runner import MypyError, MypyResult


class TestAchievement:
    """Test the Achievement dataclass."""
    
    def test_achievement_initialization_defaults(self):
        """Test Achievement initialization with default parameters."""
        achievement = Achievement(
            id="test_id",
            name="Test Achievement", 
            description="A test achievement",
            icon="🎯",
            category="testing"
        )
        
        assert achievement.id == "test_id"
        assert achievement.name == "Test Achievement"
        assert achievement.description == "A test achievement"
        assert achievement.icon == "🎯"
        assert achievement.category == "testing"
        assert achievement.earned_at is None
        assert achievement.criteria == {}
    
    def test_achievement_initialization_with_all_fields(self):
        """Test Achievement initialization with all parameters."""
        earned_time = datetime.now(timezone.utc)
        criteria = {"errors_fixed": 10}
        
        achievement = Achievement(
            id="test_id",
            name="Test Achievement",
            description="A test achievement", 
            icon="🎯",
            category="testing",
            earned_at=earned_time,
            criteria=criteria
        )
        
        assert achievement.id == "test_id"
        assert achievement.name == "Test Achievement"
        assert achievement.description == "A test achievement"
        assert achievement.icon == "🎯"
        assert achievement.category == "testing"
        assert achievement.earned_at == earned_time
        assert achievement.criteria == criteria
    
    def test_is_earned_when_not_earned(self):
        """Test is_earned returns False when achievement not earned."""
        achievement = Achievement(
            id="test_id",
            name="Test Achievement",
            description="A test achievement",
            icon="🎯", 
            category="testing"
        )
        
        assert not achievement.is_earned()
    
    def test_is_earned_when_earned(self):
        """Test is_earned returns True when achievement is earned."""
        earned_time = datetime.now(timezone.utc)
        achievement = Achievement(
            id="test_id",
            name="Test Achievement",
            description="A test achievement",
            icon="🎯",
            category="testing",
            earned_at=earned_time
        )
        
        assert achievement.is_earned()


class TestSessionStats:
    """Test the SessionStats dataclass."""
    
    def test_session_stats_initialization_defaults(self):
        """Test SessionStats initialization with default parameters."""
        started_at = datetime.now(timezone.utc)
        stats = SessionStats(
            session_id="test_session",
            started_at=started_at
        )
        
        assert stats.session_id == "test_session"
        assert stats.started_at == started_at
        assert stats.ended_at is None
        assert stats.files_checked == 0
        assert stats.errors_found == 0
        assert stats.errors_fixed == 0
        assert stats.new_errors == 0
        assert stats.error_types == {}
    
    def test_session_stats_initialization_with_all_fields(self):
        """Test SessionStats initialization with all parameters."""
        started_at = datetime.now(timezone.utc)
        ended_at = started_at + timedelta(minutes=30)
        error_types = {"no-untyped-def": 5, "attr-defined": 3}
        
        stats = SessionStats(
            session_id="test_session",
            started_at=started_at,
            ended_at=ended_at,
            files_checked=10,
            errors_found=15,
            errors_fixed=12,
            new_errors=2,
            error_types=error_types
        )
        
        assert stats.session_id == "test_session"
        assert stats.started_at == started_at
        assert stats.ended_at == ended_at
        assert stats.files_checked == 10
        assert stats.errors_found == 15
        assert stats.errors_fixed == 12
        assert stats.new_errors == 2
        assert stats.error_types == error_types
    
    def test_duration_property_with_ended_session(self):
        """Test duration property when session is ended."""
        started_at = datetime.now(timezone.utc)
        ended_at = started_at + timedelta(minutes=30)
        stats = SessionStats(
            session_id="test_session",
            started_at=started_at,
            ended_at=ended_at
        )
        
        expected_duration = (ended_at - started_at).total_seconds()
        assert stats.duration == expected_duration
    
    def test_duration_property_with_ongoing_session(self):
        """Test duration property when session is ongoing."""
        started_at = datetime.now(timezone.utc) - timedelta(minutes=15)
        stats = SessionStats(
            session_id="test_session", 
            started_at=started_at
        )
        
        # Duration should be approximately 15 minutes (900 seconds)
        assert 890 <= stats.duration <= 910  # Allow some variance for execution time
    
    def test_fix_rate_property_with_zero_errors(self):
        """Test fix_rate property when no errors found."""
        stats = SessionStats(
            session_id="test_session",
            started_at=datetime.now(timezone.utc),
            errors_found=0,
            errors_fixed=0
        )
        
        assert stats.fix_rate == 0.0
    
    def test_fix_rate_property_with_partial_fixes(self):
        """Test fix_rate property with partial error fixes."""
        stats = SessionStats(
            session_id="test_session",
            started_at=datetime.now(timezone.utc),
            errors_found=10,
            errors_fixed=7
        )
        
        assert stats.fix_rate == 70.0
    
    def test_fix_rate_property_with_all_fixes(self):
        """Test fix_rate property when all errors fixed."""
        stats = SessionStats(
            session_id="test_session",
            started_at=datetime.now(timezone.utc),
            errors_found=5,
            errors_fixed=5
        )
        
        assert stats.fix_rate == 100.0


class TestProgressData:
    """Test the ProgressData dataclass."""
    
    def test_progress_data_initialization_defaults(self):
        """Test ProgressData initialization with defaults."""
        data = ProgressData()
        
        assert data.total_errors_fixed == 0
        assert data.total_sessions == 0
        assert data.total_time_spent == 0.0
        assert data.error_history == {}
        assert data.achievements == []
        assert data.current_streak == 0
        assert data.longest_streak == 0
        assert data.last_check_date is None
        assert data.files_mastered == set()
        assert data.tutorial_progress == {}
    
    def test_progress_data_initialization_with_values(self):
        """Test ProgressData initialization with custom values."""
        achievements = [Achievement("test", "Test", "Test achievement", "🎯", "test")]
        files_mastered = {"file1.py", "file2.py"}
        tutorial_progress = {"tutorial1": 75.0, "tutorial2": 100.0}
        error_history = {"2024-01-01": {"no-untyped-def": 5}}
        
        data = ProgressData(
            total_errors_fixed=42,
            total_sessions=10,
            total_time_spent=3600.0,
            error_history=error_history,
            achievements=achievements,
            current_streak=5,
            longest_streak=12,
            last_check_date="2024-01-01",
            files_mastered=files_mastered,
            tutorial_progress=tutorial_progress
        )
        
        assert data.total_errors_fixed == 42
        assert data.total_sessions == 10
        assert data.total_time_spent == 3600.0
        assert data.error_history == error_history
        assert data.achievements == achievements
        assert data.current_streak == 5
        assert data.longest_streak == 12
        assert data.last_check_date == "2024-01-01"
        assert data.files_mastered == files_mastered
        assert data.tutorial_progress == tutorial_progress
    
    def test_to_dict_conversion(self):
        """Test to_dict method converts data correctly."""
        earned_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        achievement = Achievement(
            id="test",
            name="Test Achievement",
            description="Test",
            icon="🎯",
            category="test",
            earned_at=earned_time,
            criteria={"errors_fixed": 1}
        )
        
        data = ProgressData(
            total_errors_fixed=42,
            achievements=[achievement],
            files_mastered={"file1.py", "file2.py"}
        )
        
        result = data.to_dict()
        
        assert result["total_errors_fixed"] == 42
        assert set(result["files_mastered"]) == {"file1.py", "file2.py"}  # Converted to list but order may vary
        assert len(result["achievements"]) == 1
        
        achievement_dict = result["achievements"][0]
        assert achievement_dict["id"] == "test"
        assert achievement_dict["earned_at"] == earned_time.isoformat()
    
    def test_to_dict_with_unearned_achievement(self):
        """Test to_dict with achievement that has no earned_at date."""
        achievement = Achievement(
            id="test",
            name="Test Achievement", 
            description="Test",
            icon="🎯",
            category="test"
        )
        
        data = ProgressData(achievements=[achievement])
        result = data.to_dict()
        
        achievement_dict = result["achievements"][0]
        assert achievement_dict["earned_at"] is None
    
    def test_from_dict_creation(self):
        """Test from_dict class method creates instance correctly."""
        earned_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        dict_data = {
            "total_errors_fixed": 42,
            "total_sessions": 10,
            "total_time_spent": 3600.0,
            "error_history": {"2024-01-01": {"no-untyped-def": 5}},
            "achievements": [{
                "id": "test",
                "name": "Test Achievement",
                "description": "Test",
                "icon": "🎯",
                "category": "test",
                "earned_at": earned_time.isoformat(),
                "criteria": {"errors_fixed": 1}
            }],
            "current_streak": 5,
            "longest_streak": 12,
            "last_check_date": "2024-01-01",
            "files_mastered": ["file1.py", "file2.py"],
            "tutorial_progress": {"tutorial1": 75.0}
        }
        
        result = ProgressData.from_dict(dict_data)
        
        assert result.total_errors_fixed == 42
        assert result.total_sessions == 10
        assert result.total_time_spent == 3600.0
        assert result.error_history == {"2024-01-01": {"no-untyped-def": 5}}
        assert result.current_streak == 5
        assert result.longest_streak == 12
        assert result.last_check_date == "2024-01-01"
        assert result.files_mastered == {"file1.py", "file2.py"}  # Converted to set
        assert result.tutorial_progress == {"tutorial1": 75.0}
        
        assert len(result.achievements) == 1
        achievement = result.achievements[0]
        assert achievement.id == "test"
        assert achievement.earned_at == earned_time
    
    def test_from_dict_with_missing_fields(self):
        """Test from_dict with missing optional fields."""
        dict_data = {}
        result = ProgressData.from_dict(dict_data)
        
        assert result.total_errors_fixed == 0
        assert result.total_sessions == 0
        assert result.achievements == []
        assert result.files_mastered == set()
    
    def test_from_dict_with_unearned_achievement(self):
        """Test from_dict with achievement that has no earned_at."""
        dict_data = {
            "achievements": [{
                "id": "test",
                "name": "Test Achievement",
                "description": "Test",
                "icon": "🎯",
                "category": "test",
                "earned_at": None,
                "criteria": {"errors_fixed": 1}
            }]
        }
        
        result = ProgressData.from_dict(dict_data)
        achievement = result.achievements[0]
        assert achievement.earned_at is None


class TestProgressTracker:
    """Test the ProgressTracker class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_progress_tracker(self, temp_dir):
        """Create ProgressTracker with mocked dependencies."""
        with patch('logic.progress_tracker.ensure_directory'):
            tracker = ProgressTracker(storage_dir=temp_dir)
            yield tracker
    
    def test_initialization_with_default_storage(self):
        """Test ProgressTracker initialization with default storage location."""
        with patch('logic.progress_tracker.ensure_directory') as mock_ensure:
            tracker = ProgressTracker()
            
            assert tracker.storage_dir == Path(".stormchecker/progress")
            assert tracker.progress_file == Path(".stormchecker/progress/progress.json")
            assert tracker.sessions_dir == Path(".stormchecker/progress/sessions")
            assert tracker.current_session is None
            assert isinstance(tracker.progress_data, ProgressData)
            
            # Should call ensure_directory twice (main dir and sessions dir)
            assert mock_ensure.call_count == 2
    
    def test_initialization_with_custom_storage(self, temp_dir):
        """Test ProgressTracker initialization with custom storage location."""
        with patch('logic.progress_tracker.ensure_directory') as mock_ensure:
            tracker = ProgressTracker(storage_dir=temp_dir)
            
            assert tracker.storage_dir == temp_dir
            assert tracker.progress_file == temp_dir / "progress.json"
            assert tracker.sessions_dir == temp_dir / "sessions"
    
    def test_load_progress_with_existing_file(self, mock_progress_tracker, temp_dir):
        """Test loading progress from existing file."""
        # Create mock progress file
        progress_data = {
            "total_errors_fixed": 42,
            "total_sessions": 5,
            "achievements": []
        }
        progress_file = temp_dir / "progress.json"
        progress_file.write_text(json.dumps(progress_data))
        
        with patch.object(mock_progress_tracker, 'progress_file', progress_file):
            result = mock_progress_tracker.load_progress()
            
            assert result.total_errors_fixed == 42
            assert result.total_sessions == 5
    
    def test_load_progress_with_missing_file(self, mock_progress_tracker):
        """Test loading progress when file doesn't exist."""
        result = mock_progress_tracker.load_progress()
        
        assert isinstance(result, ProgressData)
        assert result.total_errors_fixed == 0
        assert result.total_sessions == 0
    
    def test_load_progress_with_corrupted_file(self, mock_progress_tracker, temp_dir):
        """Test loading progress with corrupted JSON file."""
        # Create corrupted JSON file
        progress_file = temp_dir / "progress.json"
        progress_file.write_text("invalid json content")
        
        with patch.object(mock_progress_tracker, 'progress_file', progress_file):
            result = mock_progress_tracker.load_progress()
            
            # Should return new ProgressData instance when file is corrupted
            assert isinstance(result, ProgressData)
            assert result.total_errors_fixed == 0
    
    def test_save_progress(self, mock_progress_tracker, temp_dir):
        """Test saving progress to file."""
        progress_file = temp_dir / "progress.json"
        mock_progress_tracker.progress_file = progress_file
        mock_progress_tracker.progress_data.total_errors_fixed = 42
        
        mock_progress_tracker.save_progress()
        
        assert progress_file.exists()
        saved_data = json.loads(progress_file.read_text())
        assert saved_data["total_errors_fixed"] == 42
    
    @patch('logic.progress_tracker.datetime')
    def test_start_session(self, mock_datetime, mock_progress_tracker):
        """Test starting a new session."""
        # Mock datetime to return consistent values
        mock_now = datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        with patch.object(mock_progress_tracker, '_update_streak') as mock_update_streak:
            session_id = mock_progress_tracker.start_session()
            
            expected_id = "session_20240115_143022"
            assert session_id == expected_id
            assert mock_progress_tracker.current_session is not None
            assert mock_progress_tracker.current_session.session_id == expected_id
            assert mock_progress_tracker.current_session.started_at == mock_now
            mock_update_streak.assert_called_once()
    
    def test_end_session_without_active_session(self, mock_progress_tracker):
        """Test ending session when no active session exists."""
        mock_result = Mock(spec=MypyResult)
        
        with pytest.raises(ValueError, match="No active session to end"):
            mock_progress_tracker.end_session(mock_result)
    
    @patch('logic.progress_tracker.datetime')
    def test_end_session_with_active_session(self, mock_datetime, mock_progress_tracker, temp_dir):
        """Test ending an active session successfully."""
        # Setup mock session
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 15, 14, 45, 0, tzinfo=timezone.utc)
        
        mock_progress_tracker.current_session = SessionStats(
            session_id="test_session",
            started_at=start_time
        )
        mock_progress_tracker.sessions_dir = temp_dir / "sessions"
        mock_progress_tracker.sessions_dir.mkdir(exist_ok=True)
        
        # Mock current time for end_session
        mock_datetime.now.return_value = end_time
        
        # Create mock MypyResult
        mock_result = Mock(spec=MypyResult)
        mock_result.files_checked = 5
        mock_result.errors = ["error1", "error2", "error3"]
        
        with patch.object(mock_progress_tracker, '_check_achievements') as mock_check:
            with patch.object(mock_progress_tracker, 'save_progress') as mock_save:
                completed_session = mock_progress_tracker.end_session(mock_result)
                
                # Verify session completed correctly
                assert completed_session.session_id == "test_session"
                assert completed_session.ended_at == end_time
                assert completed_session.files_checked == 5
                assert completed_session.errors_found == 3
                
                # Verify progress data updated
                assert mock_progress_tracker.progress_data.total_sessions == 1
                assert mock_progress_tracker.progress_data.total_time_spent == 900.0  # 15 minutes
                
                # Verify session file created
                session_file = temp_dir / "sessions" / "test_session.json"
                assert session_file.exists()
                
                # Verify methods called
                mock_check.assert_called_once()
                mock_save.assert_called_once()
                
                # Verify current session cleared
                assert mock_progress_tracker.current_session is None
    
    def test_record_fix_without_session(self, mock_progress_tracker):
        """Test recording a fix without active session."""
        mock_error = Mock(spec=MypyError)
        mock_error.error_code = "no-untyped-def"
        
        with patch('logic.progress_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
            
            mock_progress_tracker.record_fix(mock_error)
            
            assert mock_progress_tracker.progress_data.total_errors_fixed == 1
            
            # Check error history updated
            today = "2024-01-15"
            assert today in mock_progress_tracker.progress_data.error_history
            assert mock_progress_tracker.progress_data.error_history[today]["no-untyped-def"] == 1
    
    def test_record_fix_with_active_session(self, mock_progress_tracker):
        """Test recording a fix with active session."""
        # Setup active session
        mock_progress_tracker.current_session = SessionStats(
            session_id="test",
            started_at=datetime.now(timezone.utc)
        )
        
        mock_error = Mock(spec=MypyError)
        mock_error.error_code = "attr-defined"
        
        with patch('logic.progress_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
            
            mock_progress_tracker.record_fix(mock_error, fix_time=30.5)
            
            # Check session updated
            assert mock_progress_tracker.current_session.errors_fixed == 1
            assert mock_progress_tracker.current_session.error_types["attr-defined"] == 1
            
            # Check progress data updated
            assert mock_progress_tracker.progress_data.total_errors_fixed == 1
    
    def test_record_fix_with_unknown_error_code(self, mock_progress_tracker):
        """Test recording a fix with no error code."""
        mock_error = Mock(spec=MypyError)
        mock_error.error_code = None
        
        with patch('logic.progress_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
            
            mock_progress_tracker.record_fix(mock_error)
            
            today = "2024-01-15"
            assert mock_progress_tracker.progress_data.error_history[today]["unknown"] == 1
    
    def test_record_new_error_without_session(self, mock_progress_tracker):
        """Test recording new error without active session."""
        mock_error = Mock(spec=MypyError)
        
        # Should not raise error, just do nothing
        mock_progress_tracker.record_new_error(mock_error)
    
    def test_record_new_error_with_session(self, mock_progress_tracker):
        """Test recording new error with active session."""
        mock_progress_tracker.current_session = SessionStats(
            session_id="test",
            started_at=datetime.now(timezone.utc)
        )
        
        mock_error = Mock(spec=MypyError)
        mock_progress_tracker.record_new_error(mock_error)
        
        assert mock_progress_tracker.current_session.new_errors == 1
    
    def test_record_error_type_encountered(self, mock_progress_tracker):
        """Test recording error type encountered."""
        with patch('logic.progress_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
            
            with patch.object(mock_progress_tracker, 'save_progress') as mock_save:
                mock_progress_tracker.record_error_type_encountered("no-untyped-def")
                
                today = "2024-01-15"
                assert mock_progress_tracker.progress_data.error_history[today]["no-untyped-def"] == 1
                mock_save.assert_called_once()
                
                # Record same error again
                mock_progress_tracker.record_error_type_encountered("no-untyped-def")
                assert mock_progress_tracker.progress_data.error_history[today]["no-untyped-def"] == 2
    
    def test_mark_file_mastered(self, mock_progress_tracker):
        """Test marking a file as mastered."""
        mock_progress_tracker.mark_file_mastered("src/models.py")
        
        assert "src/models.py" in mock_progress_tracker.progress_data.files_mastered
    
    def test_update_tutorial_progress(self, mock_progress_tracker):
        """Test updating tutorial progress."""
        with patch.object(mock_progress_tracker, '_check_achievements') as mock_check:
            mock_progress_tracker.update_tutorial_progress("tutorial1", 75.5)
            
            assert mock_progress_tracker.progress_data.tutorial_progress["tutorial1"] == 75.5
            mock_check.assert_not_called()  # Not called for incomplete tutorial
    
    def test_update_tutorial_progress_completed(self, mock_progress_tracker):
        """Test updating tutorial progress to completion."""
        with patch.object(mock_progress_tracker, '_check_achievements') as mock_check:
            mock_progress_tracker.update_tutorial_progress("tutorial1", 100.0)
            
            assert mock_progress_tracker.progress_data.tutorial_progress["tutorial1"] == 100.0
            mock_check.assert_called_once()  # Called for completed tutorial
    
    def test_update_tutorial_progress_bounds(self, mock_progress_tracker):
        """Test tutorial progress is bounded to 0-100."""
        mock_progress_tracker.update_tutorial_progress("tutorial1", -5.0)
        assert mock_progress_tracker.progress_data.tutorial_progress["tutorial1"] == 0.0
        
        mock_progress_tracker.update_tutorial_progress("tutorial2", 150.0)
        assert mock_progress_tracker.progress_data.tutorial_progress["tutorial2"] == 100.0
    
    @patch('logic.progress_tracker.format_time_delta')
    def test_get_stats_summary(self, mock_format_time, mock_progress_tracker):
        """Test getting statistics summary."""
        # Setup test data
        mock_progress_tracker.progress_data.total_errors_fixed = 42
        mock_progress_tracker.progress_data.total_sessions = 5
        mock_progress_tracker.progress_data.total_time_spent = 3600.0
        mock_progress_tracker.progress_data.current_streak = 7
        mock_progress_tracker.progress_data.longest_streak = 15
        mock_progress_tracker.progress_data.files_mastered = {"file1.py", "file2.py"}
        mock_progress_tracker.progress_data.tutorial_progress = {"t1": 100.0, "t2": 50.0}
        mock_progress_tracker.progress_data.error_history = {
            "2024-01-01": {"no-untyped-def": 5, "attr-defined": 3},
            "2024-01-02": {"no-untyped-def": 2}
        }
        
        # Add earned achievement
        achievement = Achievement("test", "Test", "Test", "🎯", "test")
        achievement.earned_at = datetime.now(timezone.utc)
        mock_progress_tracker.progress_data.achievements = [achievement]
        
        mock_format_time.return_value = "1h 0m"
        
        with patch.object(mock_progress_tracker, '_calculate_velocity', return_value=2.5):
            result = mock_progress_tracker.get_stats_summary()
            
            assert result["total_fixes"] == 42
            assert result["total_sessions"] == 5
            assert result["total_time"] == "1h 0m"
            assert result["current_streak"] == 7
            assert result["longest_streak"] == 15
            assert result["files_mastered"] == 2
            assert result["achievements_earned"] == 1
            assert result["tutorials_completed"] == 1
            assert result["unique_error_types"] == 2  # no-untyped-def, attr-defined
            assert result["velocity"] == 2.5
            assert result["average_session_time"] == "1h 0m"
    
    def test_get_achievements_all(self, mock_progress_tracker):
        """Test getting all achievements."""
        # Mark one achievement as earned
        earned_achievement = Achievement("first_fix", "First Fix", "Test", "🎯", "test")
        earned_achievement.earned_at = datetime.now(timezone.utc)
        mock_progress_tracker.progress_data.achievements = [earned_achievement]
        
        achievements = mock_progress_tracker.get_achievements()
        
        # Should return all predefined achievements
        assert len(achievements) == len(ProgressTracker.ACHIEVEMENTS)
        
        # Find the earned achievement in the results
        earned_in_results = None
        for a in achievements:
            if a.id == "first_fix":
                earned_in_results = a
                break
        
        assert earned_in_results is not None
        assert earned_in_results.is_earned()
    
    def test_get_achievements_by_category(self, mock_progress_tracker):
        """Test getting achievements filtered by category."""
        achievements = mock_progress_tracker.get_achievements(category="errors_fixed")
        
        # All returned achievements should be in the errors_fixed category
        for achievement in achievements:
            assert achievement.category == "errors_fixed"
        
        # Should have multiple error-related achievements
        assert len(achievements) > 0
    
    @patch('logic.progress_tracker.datetime')
    def test_update_streak_first_check(self, mock_datetime, mock_progress_tracker):
        """Test updating streak for first check."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        mock_progress_tracker._update_streak()
        
        assert mock_progress_tracker.progress_data.current_streak == 1
        assert mock_progress_tracker.progress_data.longest_streak == 1
        assert mock_progress_tracker.progress_data.last_check_date == "2024-01-15"
    
    @patch('logic.progress_tracker.datetime')
    def test_update_streak_same_day(self, mock_datetime, mock_progress_tracker):
        """Test updating streak on same day (no change)."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mock_progress_tracker.progress_data.last_check_date = "2024-01-15"
        mock_progress_tracker.progress_data.current_streak = 5
        
        mock_progress_tracker._update_streak()
        
        # Should not change
        assert mock_progress_tracker.progress_data.current_streak == 5
        assert mock_progress_tracker.progress_data.last_check_date == "2024-01-15"
    
    @patch('logic.progress_tracker.datetime')
    def test_update_streak_consecutive_day(self, mock_datetime, mock_progress_tracker):
        """Test updating streak on consecutive day."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mock_progress_tracker.progress_data.last_check_date = "2024-01-14"
        mock_progress_tracker.progress_data.current_streak = 5
        mock_progress_tracker.progress_data.longest_streak = 7
        
        mock_progress_tracker._update_streak()
        
        assert mock_progress_tracker.progress_data.current_streak == 6
        assert mock_progress_tracker.progress_data.longest_streak == 7  # Not exceeded yet
        assert mock_progress_tracker.progress_data.last_check_date == "2024-01-15"
    
    @patch('logic.progress_tracker.datetime')
    def test_update_streak_broken(self, mock_datetime, mock_progress_tracker):
        """Test streak reset when broken."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mock_progress_tracker.progress_data.last_check_date = "2024-01-10"  # 5 days ago
        mock_progress_tracker.progress_data.current_streak = 5
        mock_progress_tracker.progress_data.longest_streak = 7
        
        mock_progress_tracker._update_streak()
        
        assert mock_progress_tracker.progress_data.current_streak == 1  # Reset
        assert mock_progress_tracker.progress_data.longest_streak == 7  # Preserved
        assert mock_progress_tracker.progress_data.last_check_date == "2024-01-15"
    
    @patch('logic.progress_tracker.datetime')
    def test_update_streak_new_longest(self, mock_datetime, mock_progress_tracker):
        """Test updating longest streak record."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mock_progress_tracker.progress_data.last_check_date = "2024-01-14"
        mock_progress_tracker.progress_data.current_streak = 7
        mock_progress_tracker.progress_data.longest_streak = 7
        
        mock_progress_tracker._update_streak()
        
        assert mock_progress_tracker.progress_data.current_streak == 8
        assert mock_progress_tracker.progress_data.longest_streak == 8  # New record
    
    @patch('logic.progress_tracker.datetime')
    def test_calculate_velocity(self, mock_datetime, mock_progress_tracker):
        """Test calculating velocity over recent period."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        # Setup error history for last 7 days
        mock_progress_tracker.progress_data.error_history = {
            "2024-01-09": {"no-untyped-def": 5},  # More than 7 days ago
            "2024-01-10": {"no-untyped-def": 3, "attr-defined": 2},  # 5 fixes
            "2024-01-12": {"no-untyped-def": 4},  # 4 fixes
            "2024-01-14": {"attr-defined": 6},  # 6 fixes
            "2024-01-15": {"no-untyped-def": 1}   # 1 fix
        }
        
        velocity = mock_progress_tracker._calculate_velocity(days=7)
        
        # Should count fixes from 2024-01-09 onwards (cutoff is 2024-01-08): 5 + 5 + 4 + 6 + 1 = 21 fixes  
        # Over 7 days = 21/7 = 3.0
        expected_velocity = 21.0 / 7.0
        assert abs(velocity - expected_velocity) < 0.01
    
    def test_check_achievements_no_new_achievements(self, mock_progress_tracker):
        """Test checking achievements when none are newly earned."""
        # Mark first achievement as already earned
        achievement = Achievement("first_fix", "First Fix", "Test", "🎯", "test")
        achievement.earned_at = datetime.now(timezone.utc)
        mock_progress_tracker.progress_data.achievements = [achievement]
        
        original_count = len(mock_progress_tracker.progress_data.achievements)
        
        with patch.object(mock_progress_tracker, '_meets_criteria', return_value=False):
            mock_progress_tracker._check_achievements()
            
            assert len(mock_progress_tracker.progress_data.achievements) == original_count
    
    @patch('logic.progress_tracker.datetime')
    def test_check_achievements_new_achievement_earned(self, mock_datetime, mock_progress_tracker):
        """Test checking achievements when new one is earned."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        original_count = len(mock_progress_tracker.progress_data.achievements)
        
        def mock_meets_criteria(achievement):
            return achievement.id == "first_fix"
        
        with patch.object(mock_progress_tracker, '_meets_criteria', side_effect=mock_meets_criteria):
            mock_progress_tracker._check_achievements()
            
            assert len(mock_progress_tracker.progress_data.achievements) == original_count + 1
            
            # Find the newly earned achievement
            earned = None
            for a in mock_progress_tracker.progress_data.achievements:
                if a.id == "first_fix":
                    earned = a
                    break
            
            assert earned is not None
            assert earned.is_earned()
    
    def test_meets_criteria_errors_fixed(self, mock_progress_tracker):
        """Test achievement criteria checking for errors fixed."""
        mock_progress_tracker.progress_data.total_errors_fixed = 10
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"errors_fixed": 5})
        assert mock_progress_tracker._meets_criteria(achievement)
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"errors_fixed": 15})
        assert not mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_sessions(self, mock_progress_tracker):
        """Test achievement criteria checking for sessions."""
        mock_progress_tracker.progress_data.total_sessions = 5
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"sessions": 3})
        assert mock_progress_tracker._meets_criteria(achievement)
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"sessions": 10})
        assert not mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_streak(self, mock_progress_tracker):
        """Test achievement criteria checking for streak."""
        mock_progress_tracker.progress_data.current_streak = 7
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"streak": 5})
        assert mock_progress_tracker._meets_criteria(achievement)
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"streak": 10})
        assert not mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_perfect_files(self, mock_progress_tracker):
        """Test achievement criteria checking for perfect files."""
        mock_progress_tracker.progress_data.files_mastered = {"file1.py", "file2.py", "file3.py"}
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"perfect_files": 2})
        assert mock_progress_tracker._meets_criteria(achievement)
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"perfect_files": 5})
        assert not mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_error_types(self, mock_progress_tracker):
        """Test achievement criteria checking for error types."""
        mock_progress_tracker.progress_data.error_history = {
            "2024-01-01": {"no-untyped-def": 5, "attr-defined": 3},
            "2024-01-02": {"return-value": 2}
        }
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"error_types": 3})
        assert mock_progress_tracker._meets_criteria(achievement)
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"error_types": 5})
        assert not mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_tutorials_completed_numeric(self, mock_progress_tracker):
        """Test achievement criteria checking for tutorials completed (numeric)."""
        mock_progress_tracker.progress_data.tutorial_progress = {"t1": 100.0, "t2": 75.0, "t3": 100.0}
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"tutorials_completed": 2})
        assert mock_progress_tracker._meets_criteria(achievement)
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"tutorials_completed": 3})
        assert not mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_tutorials_completed_all(self, mock_progress_tracker):
        """Test achievement criteria checking for all tutorials completed."""
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"tutorials_completed": "all"})
        # Should pass (TODO: implement proper all tutorial check)
        assert mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_clean_session_with_session(self, mock_progress_tracker):
        """Test achievement criteria checking for clean session."""
        mock_progress_tracker.current_session = SessionStats(
            session_id="test",
            started_at=datetime.now(timezone.utc),
            new_errors=0
        )
        
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"clean_session": True})
        assert mock_progress_tracker._meets_criteria(achievement)
        
        mock_progress_tracker.current_session.new_errors = 2
        assert not mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_clean_session_without_session(self, mock_progress_tracker):
        """Test achievement criteria checking for clean session without active session."""
        achievement = Achievement("test", "Test", "Test", "🎯", "test", criteria={"clean_session": True})
        # Should pass when no active session
        assert mock_progress_tracker._meets_criteria(achievement)
    
    def test_meets_criteria_complex_criteria(self, mock_progress_tracker):
        """Test achievement criteria with multiple criteria."""
        mock_progress_tracker.progress_data.total_errors_fixed = 10
        mock_progress_tracker.progress_data.total_sessions = 5
        
        # Both criteria met
        achievement = Achievement("test", "Test", "Test", "🎯", "test", 
                                criteria={"errors_fixed": 5, "sessions": 3})
        assert mock_progress_tracker._meets_criteria(achievement)
        
        # One criteria not met
        achievement = Achievement("test", "Test", "Test", "🎯", "test",
                                criteria={"errors_fixed": 15, "sessions": 3})
        assert not mock_progress_tracker._meets_criteria(achievement)
    
    @patch('logic.progress_tracker.datetime')
    def test_export_progress_report(self, mock_datetime, mock_progress_tracker, temp_dir):
        """Test exporting progress report."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 30, tzinfo=timezone.utc)
        
        # Setup test data
        achievement = Achievement("test", "Test Achievement", "Test description", "🎯", "test")
        achievement.earned_at = datetime(2024, 1, 10, tzinfo=timezone.utc)
        
        mock_progress_tracker.progress_data.achievements = [achievement]
        mock_progress_tracker.progress_data.error_history = {
            "2024-01-01": {"no-untyped-def": 5, "attr-defined": 3}
        }
        
        with patch.object(mock_progress_tracker, 'get_stats_summary') as mock_stats:
            mock_stats.return_value = {
                "total_fixes": 42,
                "total_sessions": 5,
                "velocity": 2.5
            }
            
            output_path = temp_dir / "report.md"
            report = mock_progress_tracker.export_progress_report(output_path)
            
            # Check report content
            assert "# Storm-Checker Progress Report" in report
            assert "Generated: 2024-01-15 12:30 UTC" in report
            assert "## Summary Statistics" in report
            assert "**Total Fixes**: 42" in report
            assert "## Achievements Earned" in report
            assert "🎯 **Test Achievement**" in report
            assert "## Error Type Distribution" in report
            assert "`no-untyped-def`: 5 fixes" in report
            assert "`attr-defined`: 3 fixes" in report
            
            # Check file was written
            assert output_path.exists()
            saved_content = output_path.read_text()
            assert saved_content == report
    
    def test_export_progress_report_no_data(self, mock_progress_tracker):
        """Test exporting progress report with no data."""
        with patch.object(mock_progress_tracker, 'get_stats_summary') as mock_stats:
            mock_stats.return_value = {"total_fixes": 0}
            
            report = mock_progress_tracker.export_progress_report()
            
            assert "*No achievements earned yet. Keep going!*" in report
            assert "*No errors fixed yet.*" in report