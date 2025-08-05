#!/usr/bin/env python3
"""Progress tracking and achievement system for educational gamification.

This module tracks user progress in learning and fixing type annotations,
manages achievements, and provides metrics for motivation and engagement.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from .utils import ensure_directory, format_time_delta
from .mypy_runner import MypyError, MypyResult


@dataclass
class Achievement:
    """Represents an achievement/badge in the learning system.
    
    Attributes:
        id: Unique identifier for the achievement.
        name: Display name of the achievement.
        description: Detailed description of what was achieved.
        icon: Emoji or symbol representing the achievement.
        category: Category of achievement (e.g., 'errors_fixed', 'learning').
        earned_at: When the achievement was earned.
        criteria: Dict describing the criteria for earning this achievement.
    """
    id: str
    name: str
    description: str
    icon: str
    category: str
    earned_at: Optional[datetime] = None
    criteria: Dict[str, Any] = field(default_factory=dict)
    
    def is_earned(self) -> bool:
        """Check if this achievement has been earned."""
        return self.earned_at is not None


@dataclass
class SessionStats:
    """Statistics for a single checking session.
    
    Attributes:
        session_id: Unique session identifier.
        started_at: When the session started.
        ended_at: When the session ended.
        files_checked: Number of files checked.
        errors_found: Number of errors found.
        errors_fixed: Number of errors fixed.
        new_errors: Number of new errors introduced.
        error_types: Count of each error type seen.
        duration: Session duration in seconds.
    """
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    files_checked: int = 0
    errors_found: int = 0
    errors_fixed: int = 0
    new_errors: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Calculate session duration in seconds."""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()
    
    @property
    def fix_rate(self) -> float:
        """Calculate the error fix rate (0-100)."""
        if self.errors_found == 0:
            return 0.0
        return (self.errors_fixed / self.errors_found) * 100


@dataclass
class ProgressData:
    """Overall progress data for a user/project.
    
    Attributes:
        total_errors_fixed: Lifetime count of errors fixed.
        total_sessions: Number of checking sessions.
        total_time_spent: Total time spent in seconds.
        error_history: History of errors by type and count.
        achievements: List of earned achievements.
        current_streak: Current daily streak.
        longest_streak: Longest daily streak achieved.
        last_check_date: Date of last check.
        files_mastered: Set of files with no errors.
        tutorial_progress: Progress in tutorials (tutorial_id -> completion %).
    """
    total_errors_fixed: int = 0
    total_sessions: int = 0
    total_time_spent: float = 0.0
    error_history: Dict[str, Dict[str, int]] = field(default_factory=dict)
    achievements: List[Achievement] = field(default_factory=list)
    current_streak: int = 0
    longest_streak: int = 0
    last_check_date: Optional[str] = None
    files_mastered: Set[str] = field(default_factory=set)
    tutorial_progress: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['files_mastered'] = list(self.files_mastered)
        data['achievements'] = [
            {**asdict(a), 'earned_at': a.earned_at.isoformat() if a.earned_at else None}
            for a in self.achievements
        ]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgressData':
        """Create from dictionary."""
        # Convert achievements
        achievements = []
        for a_data in data.get('achievements', []):
            earned_at = None
            if a_data.get('earned_at'):
                earned_at = datetime.fromisoformat(a_data['earned_at'])
            achievements.append(Achievement(
                id=a_data['id'],
                name=a_data['name'],
                description=a_data['description'],
                icon=a_data['icon'],
                category=a_data['category'],
                earned_at=earned_at,
                criteria=a_data.get('criteria', {})
            ))
        
        return cls(
            total_errors_fixed=data.get('total_errors_fixed', 0),
            total_sessions=data.get('total_sessions', 0),
            total_time_spent=data.get('total_time_spent', 0.0),
            error_history=data.get('error_history', {}),
            achievements=achievements,
            current_streak=data.get('current_streak', 0),
            longest_streak=data.get('longest_streak', 0),
            last_check_date=data.get('last_check_date'),
            files_mastered=set(data.get('files_mastered', [])),
            tutorial_progress=data.get('tutorial_progress', {})
        )


class ProgressTracker:
    """Tracks learning progress and manages achievements."""
    
    # Achievement definitions
    ACHIEVEMENTS = [
        # First steps
        Achievement("first_fix", "First Fix", "Fixed your first type error!", "🎯", "errors_fixed",
                   criteria={"errors_fixed": 1}),
        Achievement("first_session", "Hello Types", "Completed your first type checking session", "👋", "learning",
                   criteria={"sessions": 1}),
        
        # Error milestones
        Achievement("ten_fixes", "Decathlon", "Fixed 10 type errors", "🔟", "errors_fixed",
                   criteria={"errors_fixed": 10}),
        Achievement("fifty_fixes", "Half Century", "Fixed 50 type errors", "5️⃣0️⃣", "errors_fixed",
                   criteria={"errors_fixed": 50}),
        Achievement("hundred_fixes", "Centurion", "Fixed 100 type errors", "💯", "errors_fixed",
                   criteria={"errors_fixed": 100}),
        Achievement("thousand_fixes", "Type Master", "Fixed 1000 type errors!", "🏆", "errors_fixed",
                   criteria={"errors_fixed": 1000}),
        
        # Streak achievements
        Achievement("week_streak", "Week Warrior", "7-day checking streak", "🔥", "consistency",
                   criteria={"streak": 7}),
        Achievement("month_streak", "Monthly Master", "30-day checking streak", "🌟", "consistency",
                   criteria={"streak": 30}),
        
        # Learning achievements
        Achievement("tutorial_complete", "Student", "Completed your first tutorial", "🎓", "learning",
                   criteria={"tutorials_completed": 1}),
        Achievement("all_tutorials", "Scholar", "Completed all tutorials", "🎓", "learning",
                   criteria={"tutorials_completed": "all"}),
        
        # Speed achievements
        Achievement("speed_demon", "Speed Demon", "Fixed 10 errors in under 5 minutes", "⚡", "speed",
                   criteria={"errors_in_time": (10, 300)}),
        Achievement("quick_learner", "Quick Learner", "Fixed an error within 30 seconds of seeing it", "🚀", "speed",
                   criteria={"quick_fix": 30}),
        
        # Perfect files
        Achievement("perfect_file", "Perfectionist", "Made a file 100% type-safe", "✨", "quality",
                   criteria={"perfect_files": 1}),
        Achievement("five_perfect", "Quality Control", "Made 5 files type-safe", "⭐", "quality",
                   criteria={"perfect_files": 5}),
        
        # Error diversity
        Achievement("error_explorer", "Error Explorer", "Fixed 5 different types of errors", "🔍", "diversity",
                   criteria={"error_types": 5}),
        Achievement("error_expert", "Error Expert", "Fixed 10 different types of errors", "🎨", "diversity",
                   criteria={"error_types": 10}),
        
        # Special achievements
        Achievement("no_new_errors", "Clean Coder", "Completed a session without introducing new errors", "🧹", "quality",
                   criteria={"clean_session": True}),
        Achievement("comeback", "Comeback Kid", "Fixed errors after a week away", "💪", "motivation",
                   criteria={"comeback": 7}),
    ]
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize progress tracker.
        
        Args:
            storage_dir: Directory to store progress data. 
                        Defaults to .stormchecker/progress.
        """
        self.storage_dir = storage_dir or Path(".stormchecker/progress")
        ensure_directory(self.storage_dir)
        
        self.progress_file = self.storage_dir / "progress.json"
        self.sessions_dir = self.storage_dir / "sessions"
        ensure_directory(self.sessions_dir)
        
        self.current_session: Optional[SessionStats] = None
        self.progress_data = self.load_progress()
        
    def load_progress(self) -> ProgressData:
        """Load progress data from storage.
        
        Returns:
            Loaded progress data or new instance if not found.
            
        Example:
            >>> tracker = ProgressTracker()
            >>> data = tracker.load_progress()
            >>> print(f"Total fixes: {data.total_errors_fixed}")
            Total fixes: 42
        """
        if self.progress_file.exists():
            try:
                content = self.progress_file.read_text(encoding="utf-8")
                data = json.loads(content)
                return ProgressData.from_dict(data)
            except (json.JSONDecodeError, OSError):
                # Corrupted file, start fresh
                pass
        
        return ProgressData()
    
    def save_progress(self) -> None:
        """Save progress data to storage."""
        data = self.progress_data.to_dict()
        self.progress_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )
    
    def start_session(self) -> str:
        """Start a new checking session.
        
        Returns:
            Session ID for the new session.
            
        Example:
            >>> tracker = ProgressTracker()
            >>> session_id = tracker.start_session()
            >>> print(f"Started session: {session_id}")
            Started session: session_20240315_143022
        """
        timestamp = datetime.now(timezone.utc)
        session_id = f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = SessionStats(
            session_id=session_id,
            started_at=timestamp
        )
        
        # Update streak
        self._update_streak()
        
        return session_id
    
    def end_session(self, result: MypyResult) -> SessionStats:
        """End the current session and update progress.
        
        Args:
            result: Final MyPy result for the session.
            
        Returns:
            Completed session statistics.
            
        Example:
            >>> tracker = ProgressTracker()
            >>> tracker.start_session()
            >>> # ... do type checking ...
            >>> stats = tracker.end_session(mypy_result)
            >>> print(f"Fixed {stats.errors_fixed} errors!")
            Fixed 5 errors!
        """
        if not self.current_session:
            raise ValueError("No active session to end")
        
        self.current_session.ended_at = datetime.now(timezone.utc)
        self.current_session.files_checked = result.files_checked
        self.current_session.errors_found = len(result.errors)
        
        # Update progress data
        self.progress_data.total_sessions += 1
        self.progress_data.total_time_spent += self.current_session.duration
        
        # Save session data
        session_file = self.sessions_dir / f"{self.current_session.session_id}.json"
        session_data = {
            **asdict(self.current_session),
            'started_at': self.current_session.started_at.isoformat(),
            'ended_at': self.current_session.ended_at.isoformat() if self.current_session.ended_at else None,
        }
        session_file.write_text(json.dumps(session_data, indent=2), encoding="utf-8")
        
        # Check for new achievements
        self._check_achievements()
        
        # Save progress
        self.save_progress()
        
        completed_session = self.current_session
        self.current_session = None
        
        return completed_session
    
    def record_fix(self, error: MypyError, fix_time: Optional[float] = None) -> None:
        """Record that an error was fixed.
        
        Args:
            error: The error that was fixed.
            fix_time: Time taken to fix in seconds (for speed achievements).
            
        Example:
            >>> tracker = ProgressTracker()
            >>> tracker.record_fix(mypy_error, fix_time=25.5)
        """
        self.progress_data.total_errors_fixed += 1
        
        if self.current_session:
            self.current_session.errors_fixed += 1
            
            # Track error types
            error_type = error.error_code or "unknown"
            if error_type not in self.current_session.error_types:
                self.current_session.error_types[error_type] = 0
            self.current_session.error_types[error_type] += 1
        
        # Update error history
        error_type = error.error_code or "unknown"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today not in self.progress_data.error_history:
            self.progress_data.error_history[today] = {}
        if error_type not in self.progress_data.error_history[today]:
            self.progress_data.error_history[today][error_type] = 0
        self.progress_data.error_history[today][error_type] += 1
        
        # TODO: Track fix time for speed achievements
        
    def record_new_error(self, error: MypyError) -> None:
        """Record that a new error was introduced.
        
        Args:
            error: The new error that was introduced.
        """
        if self.current_session:
            self.current_session.new_errors += 1
    
    def record_error_type_encountered(self, error_code: str) -> None:
        """Record that a user encountered a specific error type.
        
        Args:
            error_code: The MyPy error code that was encountered.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Initialize the day if it doesn't exist
        if today not in self.progress_data.error_history:
            self.progress_data.error_history[today] = {}
        
        # Track that this error code was encountered (increment count)
        current_count = self.progress_data.error_history[today].get(error_code, 0)
        self.progress_data.error_history[today][error_code] = current_count + 1
        
        # Save progress
        self.save_progress()
    
    def mark_file_mastered(self, file_path: str) -> None:
        """Mark a file as mastered (no type errors).
        
        Args:
            file_path: Path to the mastered file.
            
        Example:
            >>> tracker = ProgressTracker()
            >>> tracker.mark_file_mastered("src/models.py")
        """
        self.progress_data.files_mastered.add(file_path)
    
    def update_tutorial_progress(self, tutorial_id: str, progress: float) -> None:
        """Update progress for a tutorial.
        
        Args:
            tutorial_id: ID of the tutorial.
            progress: Progress percentage (0-100).
            
        Example:
            >>> tracker = ProgressTracker()
            >>> tracker.update_tutorial_progress("type_annotations_basics", 75.0)
        """
        self.progress_data.tutorial_progress[tutorial_id] = min(100.0, max(0.0, progress))
        
        # Check if tutorial completed
        if progress >= 100.0:
            self._check_achievements()
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get a summary of progress statistics.
        
        Returns:
            Dictionary containing progress summary.
            
        Example:
            >>> tracker = ProgressTracker()
            >>> stats = tracker.get_stats_summary()
            >>> print(f"Total fixes: {stats['total_fixes']}")
            Total fixes: 142
        """
        # Calculate velocity (fixes per day over last 7 days)
        velocity = self._calculate_velocity()
        
        # Count unique error types
        unique_error_types = set()
        for day_errors in self.progress_data.error_history.values():
            unique_error_types.update(day_errors.keys())
        
        return {
            "total_fixes": self.progress_data.total_errors_fixed,
            "total_sessions": self.progress_data.total_sessions,
            "total_time": format_time_delta(self.progress_data.total_time_spent),
            "current_streak": self.progress_data.current_streak,
            "longest_streak": self.progress_data.longest_streak,
            "files_mastered": len(self.progress_data.files_mastered),
            "achievements_earned": len([a for a in self.progress_data.achievements if a.is_earned()]),
            "tutorials_completed": sum(1 for p in self.progress_data.tutorial_progress.values() if p >= 100),
            "unique_error_types": len(unique_error_types),
            "velocity": velocity,
            "average_session_time": format_time_delta(
                self.progress_data.total_time_spent / max(1, self.progress_data.total_sessions)
            ),
        }
    
    def get_achievements(self, category: Optional[str] = None) -> List[Achievement]:
        """Get achievements, optionally filtered by category.
        
        Args:
            category: Optional category to filter by.
            
        Returns:
            List of achievements.
            
        Example:
            >>> tracker = ProgressTracker()
            >>> speed_achievements = tracker.get_achievements("speed")
            >>> for a in speed_achievements:
            ...     print(f"{a.icon} {a.name}: {a.description}")
        """
        achievements = self.ACHIEVEMENTS.copy()
        
        # Mark which ones are earned
        earned_ids = {a.id for a in self.progress_data.achievements}
        for achievement in achievements:
            if achievement.id in earned_ids:
                # Find the earned version to get the timestamp
                for earned in self.progress_data.achievements:
                    if earned.id == achievement.id:
                        achievement.earned_at = earned.earned_at
                        break
        
        if category:
            achievements = [a for a in achievements if a.category == category]
        
        return achievements
    
    def _update_streak(self) -> None:
        """Update daily streak information."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        if self.progress_data.last_check_date == today:
            # Already checked today
            return
        
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        
        if self.progress_data.last_check_date == yesterday:
            # Continuing streak
            self.progress_data.current_streak += 1
        else:
            # Streak broken
            self.progress_data.current_streak = 1
        
        # Update longest streak
        if self.progress_data.current_streak > self.progress_data.longest_streak:
            self.progress_data.longest_streak = self.progress_data.current_streak
        
        self.progress_data.last_check_date = today
    
    def _calculate_velocity(self, days: int = 7) -> float:
        """Calculate average fixes per day over recent period.
        
        Args:
            days: Number of days to calculate over.
            
        Returns:
            Average fixes per day.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        total_fixes = 0
        for date_str, day_errors in self.progress_data.error_history.items():
            if date_str >= cutoff_str:
                total_fixes += sum(day_errors.values())
        
        return total_fixes / days
    
    def _check_achievements(self) -> None:
        """Check if any new achievements have been earned."""
        earned_ids = {a.id for a in self.progress_data.achievements}
        
        for achievement in self.ACHIEVEMENTS:
            if achievement.id in earned_ids:
                continue
            
            # Check criteria
            if self._meets_criteria(achievement):
                # Award achievement
                achievement.earned_at = datetime.now(timezone.utc)
                self.progress_data.achievements.append(achievement)
                
                # TODO: Trigger notification or celebration
    
    def _meets_criteria(self, achievement: Achievement) -> bool:
        """Check if achievement criteria are met.
        
        Args:
            achievement: Achievement to check.
            
        Returns:
            True if criteria are met.
        """
        criteria = achievement.criteria
        
        # Simple criteria checks
        if "errors_fixed" in criteria:
            if self.progress_data.total_errors_fixed < criteria["errors_fixed"]:
                return False
        
        if "sessions" in criteria:
            if self.progress_data.total_sessions < criteria["sessions"]:
                return False
        
        if "streak" in criteria:
            if self.progress_data.current_streak < criteria["streak"]:
                return False
        
        if "perfect_files" in criteria:
            if len(self.progress_data.files_mastered) < criteria["perfect_files"]:
                return False
        
        if "error_types" in criteria:
            unique_types = set()
            for day_errors in self.progress_data.error_history.values():
                unique_types.update(day_errors.keys())
            if len(unique_types) < criteria["error_types"]:
                return False
        
        if "tutorials_completed" in criteria:
            completed = sum(1 for p in self.progress_data.tutorial_progress.values() if p >= 100)
            if criteria["tutorials_completed"] == "all":
                # TODO: Check against total number of tutorials
                pass
            elif completed < criteria["tutorials_completed"]:
                return False
        
        if "clean_session" in criteria and self.current_session:
            if self.current_session.new_errors > 0:
                return False
        
        # TODO: Implement more complex criteria (speed, comeback, etc.)
        
        return True
    
    def export_progress_report(self, output_path: Optional[Path] = None) -> str:
        """Export a detailed progress report.
        
        Args:
            output_path: Optional path to save report to.
            
        Returns:
            Formatted progress report as string.
            
        Example:
            >>> tracker = ProgressTracker()
            >>> report = tracker.export_progress_report(Path("my_progress.md"))
            >>> print(report[:100])
            # Storm-Checker Progress Report
            Generated: 2024-03-15
            ...
        """
        report_lines = [
            "# Storm-Checker Progress Report",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Summary Statistics",
            ""
        ]
        
        stats = self.get_stats_summary()
        for key, value in stats.items():
            key_display = key.replace("_", " ").title()
            report_lines.append(f"- **{key_display}**: {value}")
        
        report_lines.extend([
            "",
            "## Achievements Earned",
            ""
        ])
        
        earned = [a for a in self.progress_data.achievements if a.is_earned()]
        if earned:
            for achievement in sorted(earned, key=lambda a: a.earned_at or datetime.min):
                date_str = achievement.earned_at.strftime("%Y-%m-%d") if achievement.earned_at else "Unknown"
                report_lines.append(f"- {achievement.icon} **{achievement.name}** - {achievement.description}")
                report_lines.append(f"  - Earned: {date_str}")
        else:
            report_lines.append("*No achievements earned yet. Keep going!*")
        
        report_lines.extend([
            "",
            "## Error Type Distribution",
            ""
        ])
        
        # Aggregate error types
        error_totals = defaultdict(int)
        for day_errors in self.progress_data.error_history.values():
            for error_type, count in day_errors.items():
                error_totals[error_type] += count
        
        if error_totals:
            for error_type, count in sorted(error_totals.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"- `{error_type}`: {count} fixes")
        else:
            report_lines.append("*No errors fixed yet.*")
        
        report = "\n".join(report_lines)
        
        if output_path:
            output_path.write_text(report, encoding="utf-8")
        
        return report


# TODO: Add support for team/project-wide progress tracking
# TODO: Add achievement notifications/celebrations
# TODO: Add progress visualization/charts
# TODO: Add learning path recommendations based on error patterns
# TODO: Add support for custom achievements
# TODO: Add integration with version control for tracking changes