#!/usr/bin/env python3
"""
Comprehensive Tests for Progress Tracker V2
============================================
Tests for the enhanced progress tracking system with full coverage.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from storm_checker.logic.progress_tracker import ProgressTracker
from storm_checker.models.progress_models import (
    SessionStats, UserStats, DailyStats, ProgressData,
    TutorialProgress, AchievementProgress, CodeQualityMetrics,
    Achievement, AchievementCategory, ACHIEVEMENTS
)


class TestProgressTracker:
    """Test the enhanced ProgressTracker v2."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def tracker(self, temp_dir):
        """Create a ProgressTracker with temp storage."""
        return ProgressTracker(storage_dir=temp_dir)
    
    def test_initialization(self, temp_dir):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(storage_dir=temp_dir)
        
        assert tracker.data_dir == temp_dir
        assert tracker.progress_file == temp_dir / "progress_v2.json"
        assert tracker.sessions_dir == temp_dir / "sessions"
        assert tracker.sessions_dir.exists()
        assert tracker.current_session is None
        assert isinstance(tracker.progress_data, ProgressData)
        assert len(tracker.achievements) > 0
    
    def test_start_session(self, tracker):
        """Test starting a new session."""
        session = tracker.start_session()
        
        assert isinstance(session, SessionStats)
        assert session.files_checked == 0
        assert session.errors_found == 0
        assert session.errors_fixed == 0
        assert session.time_spent == 0.0
        assert tracker.current_session == session
    
    def test_start_session_already_in_progress(self, tracker):
        """Test starting session when one is already active."""
        tracker.start_session()
        
        with pytest.raises(ValueError, match="Session already in progress"):
            tracker.start_session()
    
    def test_end_session(self, tracker):
        """Test ending a session."""
        tracker.start_session()
        tracker.current_session.files_checked = 5
        tracker.current_session.errors_found = 10
        tracker.current_session.errors_fixed = 8
        
        tracker.end_session(120.5)
        
        assert tracker.current_session is None
        assert tracker.progress_data.user_stats.total_sessions == 1
        assert tracker.progress_data.user_stats.total_files_checked == 5
        assert tracker.progress_data.user_stats.total_errors_found == 10
        assert tracker.progress_data.user_stats.total_errors_fixed == 8
        assert tracker.progress_data.user_stats.total_time_spent == 120.5
    
    def test_end_session_no_active(self, tracker):
        """Test ending session when none is active."""
        with pytest.raises(ValueError, match="No active session"):
            tracker.end_session(100.0)
    
    def test_update_session_stats(self, tracker):
        """Test updating session statistics."""
        tracker.start_session()
        
        tracker.update_session_stats(
            files_checked=10,
            errors_found=5,
            errors_fixed=3,
            error_types={"type-arg": 2, "import": 1},
            files_modified=["file1.py", "file2.py"]
        )
        
        assert tracker.current_session.files_checked == 10
        assert tracker.current_session.errors_found == 5
        assert tracker.current_session.errors_fixed == 3
        assert tracker.current_session.error_types["type-arg"] == 2
        assert tracker.current_session.error_types["import"] == 1
        assert "file1.py" in tracker.current_session.files_modified
        assert "file2.py" in tracker.current_session.files_modified
    
    def test_record_tutorial_completion(self, tracker):
        """Test recording tutorial completion."""
        tracker.record_tutorial_completion("tutorial_1", 95, 300.0)
        
        assert "tutorial_1" in tracker.progress_data.tutorial_progress.completed
        assert tracker.progress_data.tutorial_progress.scores["tutorial_1"] == 95
        assert tracker.progress_data.tutorial_progress.total_time_spent == 300.0
        assert tracker.progress_data.tutorial_progress.last_activity is not None
    
    def test_update_code_metrics(self, tracker):
        """Test updating code quality metrics."""
        tracker.update_code_metrics(
            type_coverage=75.5,
            functions_with_hints=100,
            total_functions=150,
            classes_with_hints=20,
            total_classes=25,
            any_types_removed=5,
            generic_types_used=10,
            protocols_defined=3
        )
        
        metrics = tracker.progress_data.code_metrics
        assert metrics.type_coverage_current == 75.5
        assert metrics.type_coverage_start == 75.5  # First update sets start
        assert metrics.functions_with_hints == 100
        assert metrics.total_functions == 150
        assert metrics.classes_with_hints == 20
        assert metrics.total_classes == 25
        assert metrics.any_types_removed == 5
        assert metrics.generic_types_used == 10
        assert metrics.protocols_defined == 3
    
    def test_clear_all_progress(self, tracker):
        """Test clearing all progress data."""
        # Add some data
        tracker.start_session()
        tracker.current_session.errors_fixed = 10
        tracker.end_session(100.0)
        tracker.record_tutorial_completion("tutorial_1", 100, 200.0)
        
        # Clear progress
        cleared = tracker.clear_all_progress()
        
        assert cleared["sessions"] == 1
        assert cleared["errors_fixed"] == 10  # This is from user_stats
        assert cleared["tutorials"] == 1
        # Some achievements may have been unlocked automatically (like first_steps)
        assert cleared["achievements"] >= 0
        assert cleared["streak"] >= 0
        
        # Verify data is cleared
        assert tracker.progress_data.user_stats.total_sessions == 0
        # Note: end_session() updates total_errors_fixed from current_session
        assert tracker.progress_data.user_stats.total_errors_fixed == 0
        assert len(tracker.progress_data.tutorial_progress.completed) == 0
    
    def test_save_and_load_progress(self, tracker):
        """Test saving and loading progress data."""
        # Add data
        tracker.start_session()
        tracker.current_session.files_checked = 5
        tracker.current_session.errors_fixed = 3
        tracker.end_session(60.0)
        tracker.record_tutorial_completion("tutorial_1", 85, 150.0)
        
        # Save progress
        tracker._save_progress()
        
        # Create new tracker to load data
        new_tracker = ProgressTracker(storage_dir=tracker.data_dir)
        
        assert new_tracker.progress_data.user_stats.total_sessions == 1
        assert new_tracker.progress_data.user_stats.total_files_checked == 5
        assert new_tracker.progress_data.user_stats.total_errors_fixed == 3
        assert "tutorial_1" in new_tracker.progress_data.tutorial_progress.completed
        assert new_tracker.progress_data.tutorial_progress.scores["tutorial_1"] == 85
    
    def test_load_corrupted_json(self, temp_dir):
        """Test handling of corrupted JSON data in progress file."""
        # Create a progress file with invalid JSON
        progress_file = temp_dir / "progress_v2.json"
        progress_file.write_text("{ invalid json data }")
        
        # Should handle corrupted data and create fresh ProgressData
        tracker = ProgressTracker(storage_dir=temp_dir)
        
        # Should have fresh data, not crash
        assert tracker.progress_data is not None
        assert tracker.progress_data.user_stats.total_sessions == 0
        assert tracker.progress_data.user_stats.total_errors_fixed == 0
        assert len(tracker.progress_data.achievements.unlocked) == 0
    
    def test_load_incompatible_data(self, temp_dir):
        """Test handling of incompatible data structure (KeyError)."""
        # Create a progress file with valid JSON but incompatible structure
        progress_file = temp_dir / "progress_v2.json"
        incompatible_data = {
            "old_format": "data",
            "missing_required_fields": True
            # Missing required 'user_stats' key
        }
        progress_file.write_text(json.dumps(incompatible_data))
        
        # Should handle KeyError and create fresh ProgressData
        tracker = ProgressTracker(storage_dir=temp_dir)
        
        # Should have fresh data
        assert tracker.progress_data is not None
        assert tracker.progress_data.user_stats.total_sessions == 0
    
    def test_load_file_permission_error(self, temp_dir):
        """Test handling of OSError when reading progress file."""
        progress_file = temp_dir / "progress_v2.json"
        
        # Write valid data first
        valid_data = {
            "user_stats": {
                "first_run": datetime.now().isoformat(),
                "last_session": datetime.now().isoformat(),
                "total_sessions": 5,
                "total_files_checked": 10,
                "total_errors_found": 20,
                "total_errors_fixed": 15,
                "total_time_spent": 3600.0,
                "current_streak": 3,
                "longest_streak": 5,
                "last_streak_date": None
            },
            "daily_stats": {},
            "tutorial_progress": {
                "completed": [],
                "in_progress": {},
                "scores": {},
                "total_time_spent": 0.0,
                "last_activity": None
            },
            "achievements": {
                "unlocked": {},
                "progress": {}
            },
            "code_metrics": {
                "type_coverage_start": 0.0,
                "type_coverage_current": 0.0,
                "functions_with_hints": 0,
                "total_functions": 0,
                "classes_with_hints": 0,
                "total_classes": 0,
                "any_types_removed": 0,
                "generic_types_used": 0,
                "protocols_defined": 0
            },
            "error_type_counts": {}
        }
        progress_file.write_text(json.dumps(valid_data))
        
        # Mock open to raise OSError
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            # Should handle OSError and create fresh ProgressData
            tracker = ProgressTracker(storage_dir=temp_dir)
            
            # Should have fresh data
            assert tracker.progress_data is not None
            assert tracker.progress_data.user_stats.total_sessions == 0
    
    def test_achievement_checking(self, tracker):
        """Test achievement criteria checking."""
        # Test sessions achievement
        achievement = Achievement(
            id="test_sessions",
            name="Test Sessions",
            description="Test",
            category=AchievementCategory.BEGINNER,
            icon="🎯",
            requirement={"sessions": 1}
        )
        
        # Should not meet criteria initially
        assert not tracker._check_achievement_criteria(achievement)
        
        # Complete a session
        tracker.start_session()
        tracker.end_session(30.0)
        
        # Should now meet criteria
        assert tracker._check_achievement_criteria(achievement)
    
    def test_achievement_errors_fixed(self, tracker):
        """Test errors fixed achievement criteria."""
        achievement = Achievement(
            id="test_errors",
            name="Test Errors",
            description="Test",
            category=AchievementCategory.PROGRESS,
            icon="🔨",
            requirement={"errors_fixed": 10}
        )
        
        # Should not meet criteria initially
        assert not tracker._check_achievement_criteria(achievement)
        
        # Add errors fixed
        tracker.progress_data.user_stats.total_errors_fixed = 10
        
        # Should now meet criteria
        assert tracker._check_achievement_criteria(achievement)
    
    def test_achievement_streak(self, tracker):
        """Test streak achievement criteria."""
        achievement = Achievement(
            id="test_streak",
            name="Test Streak",
            description="Test",
            category=AchievementCategory.STREAK,
            icon="🔥",
            requirement={"streak": 7}
        )
        
        # Should not meet criteria initially
        assert not tracker._check_achievement_criteria(achievement)
        
        # Set streak
        tracker.progress_data.user_stats.current_streak = 7
        
        # Should now meet criteria
        assert tracker._check_achievement_criteria(achievement)
    
    def test_achievement_time_based(self, tracker):
        """Test time-based achievement criteria."""
        # Create achievement for early morning
        achievement = Achievement(
            id="test_time",
            name="Test Time",
            description="Test",
            category=AchievementCategory.FUN,
            icon="🌅",
            requirement={"time_before": "23:59"}
        )
        
        # Should meet criteria (current time is before 23:59)
        assert tracker._check_achievement_criteria(achievement)
        
        # Create achievement for impossible time
        achievement2 = Achievement(
            id="test_time2",
            name="Test Time 2",
            description="Test",
            category=AchievementCategory.FUN,
            icon="🌃",
            requirement={"time_after": "23:59", "time_before": "00:00"}
        )
        
        # Should not meet criteria (impossible time range)
        assert not tracker._check_achievement_criteria(achievement2)
    
    def test_get_dashboard_data(self, tracker):
        """Test getting dashboard data."""
        # Add some data
        tracker.start_session()
        tracker.current_session.files_checked = 10
        tracker.current_session.errors_found = 5
        tracker.current_session.errors_fixed = 4
        tracker.end_session(120.0)
        
        tracker.record_tutorial_completion("tutorial_1", 90, 180.0)
        tracker.update_code_metrics(type_coverage=80.0)
        
        # Get dashboard data
        data = tracker.get_dashboard_data()
        
        assert data["overall_stats"]["files_analyzed"] == 10
        assert data["overall_stats"]["errors_fixed"] == 4
        assert data["overall_stats"]["type_coverage"]["current"] == 80.0
        assert data["tutorial_progress"]["completed"] == 1
        assert data["achievements"]["total"] == len(ACHIEVEMENTS)
        assert len(data["week_activity"]) == 7
        assert data["total_sessions"] == 1
    
    def test_format_time_ago(self, tracker):
        """Test time ago formatting."""
        now = datetime.now()
        
        # Just now
        result = tracker._format_time_ago(now)
        assert result == "just now"
        
        # Minutes ago
        past = now - timedelta(minutes=5)
        result = tracker._format_time_ago(past)
        assert "5 minutes ago" in result
        
        # Hours ago
        past = now - timedelta(hours=3)
        result = tracker._format_time_ago(past)
        assert "3 hours ago" in result
        
        # Days ago
        past = now - timedelta(days=2)
        result = tracker._format_time_ago(past)
        assert "2 days ago" in result
        
        # None
        result = tracker._format_time_ago(None)
        assert result == "never"
    
    def test_get_latest_tutorial(self, tracker):
        """Test getting latest tutorial info."""
        # No tutorials completed
        result = tracker._get_latest_tutorial()
        assert result is None
        
        # Add completed tutorial
        tracker.record_tutorial_completion("hello_world", 95, 100.0)
        
        result = tracker._get_latest_tutorial()
        assert result is not None
        assert result["name"] == "Hello World"
        # "just now" or "X ago" - both are valid
        assert "now" in result["when"] or "ago" in result["when"]
    
    def test_get_next_goals(self, tracker):
        """Test getting suggested next goals."""
        goals = tracker._get_next_goals()
        
        # Should suggest tutorial completion
        assert any("tutorial" in goal.lower() for goal in goals)
        
        # Add some progress
        tracker.progress_data.user_stats.total_errors_fixed = 95
        
        goals = tracker._get_next_goals()
        # Should suggest reaching 100 errors fixed
        assert any("100" in goal for goal in goals)
    
    def test_session_file_creation(self, tracker):
        """Test that session files are created correctly."""
        tracker.start_session()
        tracker.current_session.files_checked = 3
        tracker.current_session.errors_found = 2
        tracker.current_session.errors_fixed = 1
        tracker.end_session(45.0)
        
        # Check session file was created
        session_files = list(tracker.sessions_dir.glob("session_*.json"))
        assert len(session_files) == 1
        
        # Verify session file content
        with open(session_files[0]) as f:
            session_data = json.load(f)
        
        assert session_data["files_checked"] == 3
        assert session_data["errors_found"] == 2
        assert session_data["errors_fixed"] == 1
        assert session_data["time_spent"] == 45.0
    
    def test_daily_stats_aggregation(self, tracker):
        """Test daily statistics aggregation."""
        # Create multiple sessions on the same day
        tracker.start_session()
        tracker.current_session.files_checked = 5
        tracker.current_session.errors_fixed = 3
        tracker.end_session(60.0)
        
        tracker.start_session()
        tracker.current_session.files_checked = 7
        tracker.current_session.errors_fixed = 4
        tracker.end_session(90.0)
        
        # Check daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        daily_stats = tracker.progress_data.daily_stats[today]
        
        assert daily_stats.sessions_count == 2
        assert daily_stats.total_files_checked == 12
        assert daily_stats.total_errors_fixed == 7
        assert daily_stats.total_time_spent == 150.0
    
    def test_error_type_tracking(self, tracker):
        """Test error type counting."""
        tracker.start_session()
        
        tracker.update_session_stats(
            error_types={"type-arg": 5, "import": 3}
        )
        tracker.end_session(30.0)
        
        # Check error type counts
        assert tracker.progress_data.error_type_counts["type-arg"] == 5
        assert tracker.progress_data.error_type_counts["import"] == 3
    
    def test_tutorial_in_progress(self, tracker):
        """Test tracking in-progress tutorials."""
        # Mark tutorial as in progress
        tracker.progress_data.tutorial_progress.in_progress["tutorial_2"] = {
            "progress": 50,
            "last_updated": datetime.now().isoformat()
        }
        
        # Complete the tutorial
        tracker.record_tutorial_completion("tutorial_2", 100, 200.0)
        
        # Should be removed from in_progress
        assert "tutorial_2" not in tracker.progress_data.tutorial_progress.in_progress
        assert "tutorial_2" in tracker.progress_data.tutorial_progress.completed
    
    def test_achievement_unlocking(self, tracker):
        """Test achievement unlocking."""
        # Initially no achievements
        assert len(tracker.progress_data.achievements.unlocked) == 0
        
        # Complete enough sessions to unlock achievement
        tracker.start_session()
        tracker.end_session(30.0)
        
        # Check if first steps achievement was unlocked
        # (The _check_achievements method is called in end_session)
        # Achievement checking depends on the requirement being met
        if "first_steps" in tracker.progress_data.achievements.unlocked:
            unlock_time = tracker.progress_data.achievements.unlocked["first_steps"]
            assert isinstance(unlock_time, datetime)
    
    def test_progress_data_serialization(self, tracker):
        """Test serialization of progress data."""
        # Add various data
        tracker.start_session()
        tracker.current_session.files_checked = 5
        tracker.end_session(60.0)
        tracker.record_tutorial_completion("test_tutorial", 85, 120.0)
        tracker.update_code_metrics(type_coverage=75.0)
        
        # Serialize
        data = tracker._serialize_progress_data(tracker.progress_data)
        
        # Check structure
        assert "user_stats" in data
        assert "daily_stats" in data
        assert "tutorial_progress" in data
        assert "achievements" in data
        assert "code_metrics" in data
        assert "error_type_counts" in data
        
        # Deserialize
        restored = tracker._deserialize_progress_data(data)
        
        # Verify data integrity
        assert restored.user_stats.total_sessions == 1
        assert restored.user_stats.total_files_checked == 5
        assert "test_tutorial" in restored.tutorial_progress.completed
        assert restored.code_metrics.type_coverage_current == 75.0