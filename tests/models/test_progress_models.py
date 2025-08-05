"""
Tests for Progress Models
=========================
Test data models for progress tracking.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.progress_models import (
    AchievementCategory, SessionStats, DailyStats, TutorialProgress,
    Achievement, ProgressData, UserStats, AchievementProgress, CodeQualityMetrics
)


class TestAchievementCategory:
    """Test AchievementCategory enum."""
    
    def test_achievement_categories_exist(self):
        """Test that all achievement categories are defined."""
        categories = [
            AchievementCategory.BEGINNER,
            AchievementCategory.PROGRESS,
            AchievementCategory.STREAK,
            AchievementCategory.MASTERY,
            AchievementCategory.SPECIAL,
            AchievementCategory.FUN
        ]
        
        for category in categories:
            assert hasattr(category, 'value')
            assert isinstance(category.value, str)


class TestSessionStats:
    """Test SessionStats data model."""
    
    def test_session_stats_creation(self):
        """Test creating SessionStats."""
        now = datetime.now()
        stats = SessionStats(
            timestamp=now,
            files_checked=10,
            errors_found=5,
            errors_fixed=3,
            time_spent=120.5,
            error_types={"no-untyped-def": 3, "return-value": 2},
            files_modified=["main.py", "utils.py"]
        )
        
        assert stats.timestamp == now
        assert stats.files_checked == 10
        assert stats.errors_found == 5
        assert stats.errors_fixed == 3
        assert stats.time_spent == 120.5
        assert stats.error_types["no-untyped-def"] == 3
        assert len(stats.files_modified) == 2
        
    def test_session_stats_defaults(self):
        """Test SessionStats with defaults."""
        stats = SessionStats(
            timestamp=datetime.now(),
            files_checked=5,
            errors_found=2,
            errors_fixed=1,
            time_spent=60.0
        )
        
        assert stats.error_types == {}
        assert stats.files_modified == []


class TestDailyStats:
    """Test DailyStats data model."""
    
    def test_daily_stats_creation(self):
        """Test creating DailyStats."""
        stats = DailyStats(
            date="2024-01-15",
            sessions_count=3,
            total_files_checked=15,
            total_errors_found=8,
            total_errors_fixed=6,
            total_time_spent=450.5,
            unique_error_types={"no-untyped-def": 5, "assignment": 3}
        )
        
        assert stats.date == "2024-01-15"
        assert stats.sessions_count == 3
        assert stats.total_files_checked == 15
        assert stats.total_errors_found == 8
        assert stats.total_errors_fixed == 6
        assert stats.total_time_spent == 450.5
        assert stats.unique_error_types["no-untyped-def"] == 5
        
    def test_add_session_to_daily(self):
        """Test adding session stats to daily stats."""
        daily = DailyStats(
            date="2024-01-15",
            sessions_count=1,
            total_files_checked=5,
            total_errors_found=3,
            total_errors_fixed=2,
            total_time_spent=100.0,
            unique_error_types={"no-untyped-def": 2}
        )
        
        session = SessionStats(
            timestamp=datetime.now(),
            files_checked=3,
            errors_found=2,
            errors_fixed=1,
            time_spent=50.0,
            error_types={"no-untyped-def": 1, "return-value": 1}
        )
        
        daily.add_session(session)
        
        assert daily.sessions_count == 2
        assert daily.total_files_checked == 8
        assert daily.total_errors_found == 5
        assert daily.total_errors_fixed == 3
        assert daily.total_time_spent == 150.0
        assert daily.unique_error_types["no-untyped-def"] == 3
        assert daily.unique_error_types["return-value"] == 1


class TestTutorialProgress:
    """Test TutorialProgress data model."""
    
    def test_tutorial_progress_creation(self):
        """Test creating TutorialProgress."""
        progress = TutorialProgress(
            completed=["hello_world", "basics"],
            in_progress={"advanced": {"page": 3, "total": 10}},
            scores={"hello_world": 100, "basics": 85},
            total_time_spent=3600.0,
            last_activity=datetime.now()
        )
        
        assert len(progress.completed) == 2
        assert "hello_world" in progress.completed
        assert progress.scores["hello_world"] == 100
        assert progress.total_time_spent == 3600.0
        
    def test_average_score_calculation(self):
        """Test average score calculation."""
        progress = TutorialProgress(
            scores={"tutorial1": 80, "tutorial2": 90, "tutorial3": 100}
        )
        
        assert progress.average_score == 90.0
        
    def test_average_score_empty(self):
        """Test average score with no scores."""
        progress = TutorialProgress()
        assert progress.average_score == 0.0


class TestAchievement:
    """Test Achievement data model."""
    
    def test_achievement_creation(self):
        """Test creating Achievement."""
        achievement = Achievement(
            id="first_error",
            name="First Steps",
            description="Fix your first type error",
            category=AchievementCategory.BEGINNER,
            icon="🎯",
            requirement={"errors_fixed": 1},
            secret=False,
            points=10
        )
        
        assert achievement.id == "first_error"
        assert achievement.name == "First Steps"
        assert achievement.category == AchievementCategory.BEGINNER
        assert achievement.icon == "🎯"
        assert achievement.points == 10
        assert achievement.requirement["errors_fixed"] == 1




class TestProgressData:
    """Test ProgressData data model."""
    
    def test_progress_data_creation(self):
        """Test creating ProgressData."""
        from datetime import datetime
        now = datetime.now()
        
        user_stats = UserStats(
            first_run=now,
            last_session=now,
            total_sessions=10,
            total_files_checked=50,
            total_errors_found=100,
            total_errors_fixed=75,
            total_time_spent=3600.0,
            current_streak=3,
            longest_streak=7
        )
        
        progress = ProgressData(
            user_stats=user_stats,
            daily_stats={
                "2024-01-15": DailyStats(
                    date="2024-01-15",
                    sessions_count=2,
                    total_files_checked=10,
                    total_errors_found=15,
                    total_errors_fixed=12,
                    total_time_spent=600.0
                )
            }
        )
        
        assert progress.user_stats.total_errors_found == 100
        assert progress.user_stats.total_errors_fixed == 75
        assert progress.user_stats.fix_rate == 75.0
        assert progress.user_stats.current_streak == 3
        assert len(progress.daily_stats) == 1
        
    def test_progress_data_add_session(self):
        """Test adding session to progress data."""
        from datetime import datetime
        now = datetime.now()
        
        user_stats = UserStats(
            first_run=now,
            last_session=now,
            total_sessions=0,
            total_files_checked=0,
            total_errors_found=0,
            total_errors_fixed=0,
            total_time_spent=0.0
        )
        
        progress = ProgressData(user_stats=user_stats)
        
        session = SessionStats(
            timestamp=now,
            files_checked=5,
            errors_found=10,
            errors_fixed=8,
            time_spent=300.0,
            error_types={"no-untyped-def": 5, "return-value": 5}
        )
        
        progress.add_session(session)
        
        assert progress.user_stats.total_sessions == 1
        assert progress.user_stats.total_files_checked == 5
        assert progress.user_stats.total_errors_found == 10
        assert progress.user_stats.total_errors_fixed == 8
        assert progress.user_stats.total_time_spent == 300.0
    
    def test_progress_data_streak_tracking(self):
        """Test streak tracking functionality."""
        progress = ProgressData(
            user_stats=UserStats(
                first_run=datetime(2024, 1, 1),
                last_session=datetime(2024, 1, 1)
            )
        )
        
        # First session - should start streak
        session1 = SessionStats(
            timestamp=datetime(2024, 1, 15, 10, 0),
            files_checked=5,
            errors_found=3,
            errors_fixed=2,
            time_spent=100.0
        )
        progress.add_session(session1)
        assert progress.user_stats.current_streak == 1
        assert progress.user_stats.last_streak_date == "2024-01-15"
        
        # Same day session - should not increment streak
        session2 = SessionStats(
            timestamp=datetime(2024, 1, 15, 14, 0),
            files_checked=3,
            errors_found=2,
            errors_fixed=1,
            time_spent=50.0
        )
        progress.add_session(session2)
        assert progress.user_stats.current_streak == 1
        assert progress.user_stats.last_streak_date == "2024-01-15"
        
        # Next day session - should continue streak
        session3 = SessionStats(
            timestamp=datetime(2024, 1, 16, 11, 0),
            files_checked=4,
            errors_found=2,
            errors_fixed=2,
            time_spent=80.0
        )
        progress.add_session(session3)
        assert progress.user_stats.current_streak == 2
        assert progress.user_stats.last_streak_date == "2024-01-16"
        
        # Gap in days - should reset streak
        session4 = SessionStats(
            timestamp=datetime(2024, 1, 20, 9, 0),
            files_checked=6,
            errors_found=4,
            errors_fixed=3,
            time_spent=120.0
        )
        progress.add_session(session4)
        assert progress.user_stats.current_streak == 1
        assert progress.user_stats.last_streak_date == "2024-01-20"


class TestUserStats:
    """Test UserStats calculations."""
    
    def test_average_errors_per_file_normal(self):
        """Test average errors per file calculation."""
        stats = UserStats(
            first_run=datetime.now(),
            last_session=datetime.now(),
            total_files_checked=10,
            total_errors_found=25
        )
        assert stats.average_errors_per_file == 2.5
    
    def test_average_errors_per_file_zero_files(self):
        """Test average errors per file with no files checked."""
        stats = UserStats(
            first_run=datetime.now(),
            last_session=datetime.now(),
            total_files_checked=0,
            total_errors_found=0
        )
        assert stats.average_errors_per_file == 0.0
    
    def test_fix_rate_normal(self):
        """Test fix rate calculation."""
        stats = UserStats(
            first_run=datetime.now(),
            last_session=datetime.now(),
            total_errors_found=20,
            total_errors_fixed=15
        )
        assert stats.fix_rate == 75.0
    
    def test_fix_rate_zero_errors(self):
        """Test fix rate with no errors found."""
        stats = UserStats(
            first_run=datetime.now(),
            last_session=datetime.now(),
            total_errors_found=0,
            total_errors_fixed=0
        )
        assert stats.fix_rate == 0.0


class TestAchievementProgress:
    """Test AchievementProgress functionality."""
    
    def test_unlock_achievement(self):
        """Test unlocking an achievement."""
        progress = AchievementProgress()
        
        # Should not be unlocked initially
        assert "first_type_hint" not in progress.unlocked
        
        # Unlock achievement
        progress.unlock_achievement("first_type_hint")
        
        # Should now be unlocked
        assert "first_type_hint" in progress.unlocked
        assert isinstance(progress.unlocked["first_type_hint"], datetime)
    
    def test_unlock_achievement_idempotent(self):
        """Test that unlocking an achievement twice doesn't change timestamp."""
        progress = AchievementProgress()
        
        # Unlock first time
        progress.unlock_achievement("streak_3")
        first_time = progress.unlocked["streak_3"]
        
        # Small delay to ensure different timestamp if it would change
        import time
        time.sleep(0.01)
        
        # Unlock again
        progress.unlock_achievement("streak_3")
        second_time = progress.unlocked["streak_3"]
        
        # Timestamp should not change
        assert first_time == second_time
    
    def test_update_progress(self):
        """Test updating achievement progress."""
        progress = AchievementProgress()
        
        # Update progress
        progress.update_progress("type_master", 75, 100)
        
        # Check stored values
        assert "type_master" in progress.progress
        assert progress.progress["type_master"]["current"] == 75
        assert progress.progress["type_master"]["target"] == 100
        assert progress.progress["type_master"]["percentage"] == 75.0
    
    def test_update_progress_zero_target(self):
        """Test updating progress with zero target."""
        progress = AchievementProgress()
        
        # Update with zero target
        progress.update_progress("special_achievement", 10, 0)
        
        # Should handle division by zero
        assert progress.progress["special_achievement"]["percentage"] == 0


class TestCodeQualityMetrics:
    """Test CodeQualityMetrics calculations."""
    
    def test_type_coverage_improvement(self):
        """Test type coverage improvement calculation."""
        metrics = CodeQualityMetrics(
            type_coverage_start=45.5,
            type_coverage_current=78.3
        )
        assert metrics.type_coverage_improvement == 32.8
    
    def test_function_coverage_normal(self):
        """Test function coverage calculation."""
        metrics = CodeQualityMetrics(
            functions_with_hints=80,
            total_functions=100
        )
        assert metrics.function_coverage == 80.0
    
    def test_function_coverage_zero_functions(self):
        """Test function coverage with no functions."""
        metrics = CodeQualityMetrics(
            functions_with_hints=0,
            total_functions=0
        )
        assert metrics.function_coverage == 0.0