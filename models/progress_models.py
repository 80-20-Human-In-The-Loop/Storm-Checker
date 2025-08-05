#!/usr/bin/env python3
"""
Progress Data Models for Storm-Checker
======================================
Data structures for tracking user progress, achievements, and statistics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


class AchievementCategory(Enum):
    """Categories for achievements."""
    BEGINNER = "beginner"
    PROGRESS = "progress"
    STREAK = "streak"
    MASTERY = "mastery"
    SPECIAL = "special"
    FUN = "fun"


@dataclass
class SessionStats:
    """Statistics for a single checking session."""
    timestamp: datetime
    files_checked: int
    errors_found: int
    errors_fixed: int
    time_spent: float  # seconds
    error_types: Dict[str, int] = field(default_factory=dict)
    files_modified: List[str] = field(default_factory=list)


@dataclass
class DailyStats:
    """Aggregated daily statistics."""
    date: str  # YYYY-MM-DD
    sessions_count: int
    total_files_checked: int
    total_errors_found: int
    total_errors_fixed: int
    total_time_spent: float
    unique_error_types: Dict[str, int] = field(default_factory=dict)
    
    def add_session(self, session: SessionStats) -> None:
        """Add a session's stats to daily totals."""
        self.sessions_count += 1
        self.total_files_checked += session.files_checked
        self.total_errors_found += session.errors_found
        self.total_errors_fixed += session.errors_fixed
        self.total_time_spent += session.time_spent
        
        # Merge error types
        for error_type, count in session.error_types.items():
            self.unique_error_types[error_type] = (
                self.unique_error_types.get(error_type, 0) + count
            )


@dataclass
class TutorialProgress:
    """Progress tracking for tutorials."""
    completed: List[str] = field(default_factory=list)
    in_progress: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    scores: Dict[str, int] = field(default_factory=dict)
    total_time_spent: float = 0.0
    last_activity: Optional[datetime] = None
    
    @property
    def average_score(self) -> float:
        """Calculate average score across completed tutorials."""
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)


@dataclass
class Achievement:
    """Achievement definition."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    icon: str
    requirement: Dict[str, Any]  # e.g., {"errors_fixed": 100}
    secret: bool = False
    points: int = 10


@dataclass
class AchievementProgress:
    """Track progress towards achievements."""
    unlocked: Dict[str, datetime] = field(default_factory=dict)
    progress: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def unlock_achievement(self, achievement_id: str) -> None:
        """Mark an achievement as unlocked."""
        if achievement_id not in self.unlocked:
            self.unlocked[achievement_id] = datetime.now()
            
    def update_progress(self, achievement_id: str, current: Any, target: Any) -> None:
        """Update progress towards an achievement."""
        self.progress[achievement_id] = {
            "current": current,
            "target": target,
            "percentage": (current / target * 100) if target > 0 else 0
        }


@dataclass
class UserStats:
    """Overall user statistics."""
    first_run: datetime
    last_session: datetime
    total_sessions: int = 0
    total_files_checked: int = 0
    total_errors_found: int = 0
    total_errors_fixed: int = 0
    total_time_spent: float = 0.0  # seconds
    current_streak: int = 0
    longest_streak: int = 0
    last_streak_date: Optional[str] = None  # YYYY-MM-DD
    
    @property
    def average_errors_per_file(self) -> float:
        """Calculate average errors per file."""
        if self.total_files_checked == 0:
            return 0.0
        return self.total_errors_found / self.total_files_checked
    
    @property
    def fix_rate(self) -> float:
        """Calculate error fix rate percentage."""
        if self.total_errors_found == 0:
            return 0.0
        return (self.total_errors_fixed / self.total_errors_found) * 100


@dataclass
class CodeQualityMetrics:
    """Track code quality improvements."""
    type_coverage_start: float = 0.0
    type_coverage_current: float = 0.0
    functions_with_hints: int = 0
    total_functions: int = 0
    classes_with_hints: int = 0
    total_classes: int = 0
    any_types_removed: int = 0
    generic_types_used: int = 0
    protocols_defined: int = 0
    
    @property
    def type_coverage_improvement(self) -> float:
        """Calculate type coverage improvement."""
        return self.type_coverage_current - self.type_coverage_start
    
    @property
    def function_coverage(self) -> float:
        """Calculate function type hint coverage."""
        if self.total_functions == 0:
            return 0.0
        return (self.functions_with_hints / self.total_functions) * 100


@dataclass
class ProgressData:
    """Complete progress data structure."""
    user_stats: UserStats
    daily_stats: Dict[str, DailyStats] = field(default_factory=dict)
    tutorial_progress: TutorialProgress = field(default_factory=TutorialProgress)
    achievements: AchievementProgress = field(default_factory=AchievementProgress)
    code_metrics: CodeQualityMetrics = field(default_factory=CodeQualityMetrics)
    error_type_counts: Dict[str, int] = field(default_factory=dict)
    
    def add_session(self, session: SessionStats) -> None:
        """Add a new session to progress data."""
        # Update user stats
        self.user_stats.total_sessions += 1
        self.user_stats.total_files_checked += session.files_checked
        self.user_stats.total_errors_found += session.errors_found
        self.user_stats.total_errors_fixed += session.errors_fixed
        self.user_stats.total_time_spent += session.time_spent
        self.user_stats.last_session = session.timestamp
        
        # Update daily stats
        date_str = session.timestamp.strftime("%Y-%m-%d")
        if date_str not in self.daily_stats:
            self.daily_stats[date_str] = DailyStats(
                date=date_str,
                sessions_count=0,
                total_files_checked=0,
                total_errors_found=0,
                total_errors_fixed=0,
                total_time_spent=0.0
            )
        self.daily_stats[date_str].add_session(session)
        
        # Update error type counts
        for error_type, count in session.error_types.items():
            self.error_type_counts[error_type] = (
                self.error_type_counts.get(error_type, 0) + count
            )
        
        # Update streak
        self._update_streak(date_str)
    
    def _update_streak(self, date_str: str) -> None:
        """Update streak information."""
        if self.user_stats.last_streak_date == date_str:
            return  # Already counted today
            
        yesterday = (datetime.strptime(date_str, "%Y-%m-%d") - 
                    timedelta(days=1)).strftime("%Y-%m-%d")
        
        if self.user_stats.last_streak_date == yesterday:
            # Continue streak
            self.user_stats.current_streak += 1
        else:
            # Start new streak
            self.user_stats.current_streak = 1
            
        self.user_stats.last_streak_date = date_str
        self.user_stats.longest_streak = max(
            self.user_stats.longest_streak,
            self.user_stats.current_streak
        )


# Pre-defined achievements
ACHIEVEMENTS = [
    # Beginner achievements
    Achievement(
        id="first_steps",
        name="First Steps",
        description="Run your first MyPy check",
        category=AchievementCategory.BEGINNER,
        icon="🚶",
        requirement={"sessions": 1},
        points=5
    ),
    Achievement(
        id="tutorial_starter",
        name="Tutorial Starter",
        description="Complete your first tutorial",
        category=AchievementCategory.BEGINNER,
        icon="📚",
        requirement={"tutorials_completed": 1},
        points=10
    ),
    
    # Progress achievements
    Achievement(
        id="error_crusher_10",
        name="Error Crusher",
        description="Fix 10 type errors",
        category=AchievementCategory.PROGRESS,
        icon="🔨",
        requirement={"errors_fixed": 10},
        points=10
    ),
    Achievement(
        id="error_crusher_100",
        name="Error Destroyer",
        description="Fix 100 type errors",
        category=AchievementCategory.PROGRESS,
        icon="💪",
        requirement={"errors_fixed": 100},
        points=25
    ),
    Achievement(
        id="error_crusher_1000",
        name="Error Annihilator",
        description="Fix 1000 type errors",
        category=AchievementCategory.PROGRESS,
        icon="🏆",
        requirement={"errors_fixed": 1000},
        points=100
    ),
    
    # Streak achievements
    Achievement(
        id="consistent_coder",
        name="Consistent Coder",
        description="Check code 7 days in a row",
        category=AchievementCategory.STREAK,
        icon="🔥",
        requirement={"streak": 7},
        points=20
    ),
    Achievement(
        id="type_safe_month",
        name="Type Safe Month",
        description="30 day checking streak",
        category=AchievementCategory.STREAK,
        icon="📅",
        requirement={"streak": 30},
        points=50
    ),
    
    # Mastery achievements
    Achievement(
        id="tutorial_master",
        name="Tutorial Master",
        description="Complete all tutorials",
        category=AchievementCategory.MASTERY,
        icon="🎓",
        requirement={"all_tutorials": True},
        points=50
    ),
    Achievement(
        id="zero_errors",
        name="Zero Errors Hero",
        description="Achieve 0 errors in 10+ files",
        category=AchievementCategory.MASTERY,
        icon="✨",
        requirement={"zero_error_files": 10},
        points=30
    ),
    
    # Fun achievements
    Achievement(
        id="night_owl",
        name="Night Owl",
        description="Run checks after midnight",
        category=AchievementCategory.FUN,
        icon="🦉",
        requirement={"time_after": "00:00", "time_before": "05:00"},
        points=5,
        secret=True
    ),
    Achievement(
        id="early_bird",
        name="Early Bird",
        description="Run checks before 6 AM",
        category=AchievementCategory.FUN,
        icon="🐦",
        requirement={"time_before": "06:00"},
        points=5,
        secret=True
    ),
]