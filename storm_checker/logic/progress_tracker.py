#!/usr/bin/env python3
"""Enhanced Progress Tracking System for Storm-Checker.

This module provides comprehensive progress tracking including:
- Detailed session and daily statistics
- Achievement system with multiple categories
- Tutorial progress integration
- Code quality metrics
- Cross-platform data storage
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
from pathlib import Path

from .utils import get_data_directory, ensure_directory, format_time_delta
from storm_checker.models.progress_models import (
    ProgressData, UserStats, SessionStats, DailyStats,
    TutorialProgress, AchievementProgress, CodeQualityMetrics,
    Achievement, AchievementCategory, ACHIEVEMENTS
)


class ProgressTracker:
    """Enhanced progress tracking with comprehensive metrics."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize the enhanced progress tracker."""
        # Use cross-platform data directory
        if storage_dir:
            self.data_dir = ensure_directory(storage_dir)
        else:
            self.data_dir = ensure_directory(get_data_directory() / "progress")
        self.progress_file = self.data_dir / "progress_v2.json"
        self.sessions_dir = ensure_directory(self.data_dir / "sessions")
        
        # Load or create progress data
        self.progress_data = self._load_progress()
        self.current_session: Optional[SessionStats] = None
        
        # Achievement engine
        self.achievements = {a.id: a for a in ACHIEVEMENTS}
        
    def _load_progress(self) -> ProgressData:
        """Load progress data from disk."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    return self._deserialize_progress_data(data)
            except (json.JSONDecodeError, OSError, KeyError):
                # Corrupted or incompatible data
                pass
        
        # Create new progress data
        now = datetime.now()
        return ProgressData(
            user_stats=UserStats(
                first_run=now,
                last_session=now
            )
        )
    
    def _save_progress(self) -> None:
        """Save progress data to disk."""
        data = self._serialize_progress_data(self.progress_data)
        with open(self.progress_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _serialize_progress_data(self, progress: ProgressData) -> Dict[str, Any]:
        """Serialize progress data for JSON storage."""
        return {
            "user_stats": {
                "first_run": progress.user_stats.first_run.isoformat(),
                "last_session": progress.user_stats.last_session.isoformat(),
                "total_sessions": progress.user_stats.total_sessions,
                "total_files_checked": progress.user_stats.total_files_checked,
                "total_errors_found": progress.user_stats.total_errors_found,
                "total_errors_fixed": progress.user_stats.total_errors_fixed,
                "total_time_spent": progress.user_stats.total_time_spent,
                "current_streak": progress.user_stats.current_streak,
                "longest_streak": progress.user_stats.longest_streak,
                "last_streak_date": progress.user_stats.last_streak_date
            },
            "daily_stats": {
                date: {
                    "date": stats.date,
                    "sessions_count": stats.sessions_count,
                    "total_files_checked": stats.total_files_checked,
                    "total_errors_found": stats.total_errors_found,
                    "total_errors_fixed": stats.total_errors_fixed,
                    "total_time_spent": stats.total_time_spent,
                    "unique_error_types": stats.unique_error_types
                }
                for date, stats in progress.daily_stats.items()
            },
            "tutorial_progress": {
                "completed": progress.tutorial_progress.completed,
                "in_progress": progress.tutorial_progress.in_progress,
                "scores": progress.tutorial_progress.scores,
                "total_time_spent": progress.tutorial_progress.total_time_spent,
                "last_activity": progress.tutorial_progress.last_activity.isoformat() 
                    if progress.tutorial_progress.last_activity else None
            },
            "achievements": {
                "unlocked": {
                    aid: dt.isoformat() for aid, dt in progress.achievements.unlocked.items()
                },
                "progress": progress.achievements.progress
            },
            "code_metrics": {
                "type_coverage_start": progress.code_metrics.type_coverage_start,
                "type_coverage_current": progress.code_metrics.type_coverage_current,
                "functions_with_hints": progress.code_metrics.functions_with_hints,
                "total_functions": progress.code_metrics.total_functions,
                "classes_with_hints": progress.code_metrics.classes_with_hints,
                "total_classes": progress.code_metrics.total_classes,
                "any_types_removed": progress.code_metrics.any_types_removed,
                "generic_types_used": progress.code_metrics.generic_types_used,
                "protocols_defined": progress.code_metrics.protocols_defined
            },
            "error_type_counts": progress.error_type_counts
        }
    
    def _deserialize_progress_data(self, data: Dict[str, Any]) -> ProgressData:
        """Deserialize progress data from JSON."""
        # User stats
        user_stats_data = data["user_stats"]
        user_stats = UserStats(
            first_run=datetime.fromisoformat(user_stats_data["first_run"]),
            last_session=datetime.fromisoformat(user_stats_data["last_session"]),
            total_sessions=user_stats_data["total_sessions"],
            total_files_checked=user_stats_data["total_files_checked"],
            total_errors_found=user_stats_data["total_errors_found"],
            total_errors_fixed=user_stats_data["total_errors_fixed"],
            total_time_spent=user_stats_data["total_time_spent"],
            current_streak=user_stats_data["current_streak"],
            longest_streak=user_stats_data["longest_streak"],
            last_streak_date=user_stats_data.get("last_streak_date")
        )
        
        # Daily stats
        daily_stats = {}
        for date, stats_data in data.get("daily_stats", {}).items():
            daily_stats[date] = DailyStats(
                date=stats_data["date"],
                sessions_count=stats_data["sessions_count"],
                total_files_checked=stats_data["total_files_checked"],
                total_errors_found=stats_data["total_errors_found"],
                total_errors_fixed=stats_data["total_errors_fixed"],
                total_time_spent=stats_data["total_time_spent"],
                unique_error_types=stats_data.get("unique_error_types", {})
            )
        
        # Tutorial progress
        tutorial_data = data.get("tutorial_progress", {})
        tutorial_progress = TutorialProgress(
            completed=tutorial_data.get("completed", []),
            in_progress=tutorial_data.get("in_progress", {}),
            scores=tutorial_data.get("scores", {}),
            total_time_spent=tutorial_data.get("total_time_spent", 0.0),
            last_activity=datetime.fromisoformat(tutorial_data["last_activity"]) 
                if tutorial_data.get("last_activity") else None
        )
        
        # Achievements
        achievement_data = data.get("achievements", {})
        achievements = AchievementProgress(
            unlocked={
                aid: datetime.fromisoformat(dt) 
                for aid, dt in achievement_data.get("unlocked", {}).items()
            },
            progress=achievement_data.get("progress", {})
        )
        
        # Code metrics
        metrics_data = data.get("code_metrics", {})
        code_metrics = CodeQualityMetrics(
            type_coverage_start=metrics_data.get("type_coverage_start", 0.0),
            type_coverage_current=metrics_data.get("type_coverage_current", 0.0),
            functions_with_hints=metrics_data.get("functions_with_hints", 0),
            total_functions=metrics_data.get("total_functions", 0),
            classes_with_hints=metrics_data.get("classes_with_hints", 0),
            total_classes=metrics_data.get("total_classes", 0),
            any_types_removed=metrics_data.get("any_types_removed", 0),
            generic_types_used=metrics_data.get("generic_types_used", 0),
            protocols_defined=metrics_data.get("protocols_defined", 0)
        )
        
        return ProgressData(
            user_stats=user_stats,
            daily_stats=daily_stats,
            tutorial_progress=tutorial_progress,
            achievements=achievements,
            code_metrics=code_metrics,
            error_type_counts=data.get("error_type_counts", {})
        )
    
    def start_session(self) -> SessionStats:
        """Start a new checking session.
        
        Returns:
            SessionStats for the new session
        """
        if self.current_session:
            raise ValueError("Session already in progress")
        
        self.current_session = SessionStats(
            timestamp=datetime.now(),
            files_checked=0,
            errors_found=0,
            errors_fixed=0,
            time_spent=0.0
        )
        
        return self.current_session
    
    def end_session(self, time_spent: float) -> None:
        """End the current session and update progress.
        
        Args:
            time_spent: Time spent in seconds
        """
        if not self.current_session:
            raise ValueError("No active session")
        
        self.current_session.time_spent = time_spent
        
        # Add to progress data
        self.progress_data.add_session(self.current_session)
        
        # Check achievements
        self._check_achievements()
        
        # Save session details
        session_file = self.sessions_dir / f"session_{self.current_session.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(session_file, 'w') as f:
            json.dump({
                "timestamp": self.current_session.timestamp.isoformat(),
                "files_checked": self.current_session.files_checked,
                "errors_found": self.current_session.errors_found,
                "errors_fixed": self.current_session.errors_fixed,
                "time_spent": self.current_session.time_spent,
                "error_types": self.current_session.error_types,
                "files_modified": self.current_session.files_modified
            }, f, indent=2)
        
        # Save progress
        self._save_progress()
        
        self.current_session = None
    
    def update_session_stats(
        self,
        files_checked: Optional[int] = None,
        errors_found: Optional[int] = None,
        errors_fixed: Optional[int] = None,
        error_types: Optional[Dict[str, int]] = None,
        files_modified: Optional[List[str]] = None
    ) -> None:
        """Update current session statistics."""
        if not self.current_session:
            raise ValueError("No active session")
        
        if files_checked is not None:
            self.current_session.files_checked = files_checked
        if errors_found is not None:
            self.current_session.errors_found = errors_found
        if errors_fixed is not None:
            self.current_session.errors_fixed = errors_fixed
        if error_types is not None:
            self.current_session.error_types.update(error_types)
        if files_modified is not None:
            self.current_session.files_modified.extend(files_modified)
    
    def record_tutorial_completion(
        self,
        tutorial_id: str,
        score: int,
        time_spent: float
    ) -> None:
        """Record tutorial completion."""
        self.progress_data.tutorial_progress.completed.append(tutorial_id)
        self.progress_data.tutorial_progress.scores[tutorial_id] = score
        self.progress_data.tutorial_progress.total_time_spent += time_spent
        self.progress_data.tutorial_progress.last_activity = datetime.now()
        
        # Remove from in_progress if it was there
        self.progress_data.tutorial_progress.in_progress.pop(tutorial_id, None)
        
        # Check achievements
        self._check_achievements()
        self._save_progress()
    
    def update_code_metrics(
        self,
        type_coverage: Optional[float] = None,
        functions_with_hints: Optional[int] = None,
        total_functions: Optional[int] = None,
        classes_with_hints: Optional[int] = None,
        total_classes: Optional[int] = None,
        any_types_removed: Optional[int] = None,
        generic_types_used: Optional[int] = None,
        protocols_defined: Optional[int] = None
    ) -> None:
        """Update code quality metrics."""
        metrics = self.progress_data.code_metrics
        
        # Set initial coverage if not set
        if metrics.type_coverage_start == 0.0 and type_coverage is not None:
            metrics.type_coverage_start = type_coverage
        
        if type_coverage is not None:
            metrics.type_coverage_current = type_coverage
        if functions_with_hints is not None:
            metrics.functions_with_hints = functions_with_hints
        if total_functions is not None:
            metrics.total_functions = total_functions
        if classes_with_hints is not None:
            metrics.classes_with_hints = classes_with_hints
        if total_classes is not None:
            metrics.total_classes = total_classes
        if any_types_removed is not None:
            metrics.any_types_removed += any_types_removed
        if generic_types_used is not None:
            metrics.generic_types_used = generic_types_used
        if protocols_defined is not None:
            metrics.protocols_defined = protocols_defined
        
        self._save_progress()
    
    def _check_achievements(self) -> None:
        """Check and unlock new achievements."""
        for achievement_id, achievement in self.achievements.items():
            if achievement_id in self.progress_data.achievements.unlocked:
                continue
            
            if self._check_achievement_criteria(achievement):
                self.progress_data.achievements.unlock_achievement(achievement_id)
    
    def _check_achievement_criteria(self, achievement: Achievement) -> bool:
        """Check if achievement criteria are met."""
        req = achievement.requirement
        
        # Session-based achievements
        if "sessions" in req:
            if self.progress_data.user_stats.total_sessions < req["sessions"]:
                return False
        
        # Error fixing achievements
        if "errors_fixed" in req:
            if self.progress_data.user_stats.total_errors_fixed < req["errors_fixed"]:
                return False
        
        # Tutorial achievements
        if "tutorials_completed" in req:
            completed_count = len(self.progress_data.tutorial_progress.completed)
            if req["tutorials_completed"] == "all":
                # TODO: Get total tutorial count from somewhere
                return False
            elif completed_count < req["tutorials_completed"]:
                return False
        
        # Streak achievements
        if "streak" in req:
            if self.progress_data.user_stats.current_streak < req["streak"]:
                return False
        
        # Time-based achievements
        if "time_after" in req or "time_before" in req:
            current_time = datetime.now().time()
            if "time_after" in req:
                after_time = datetime.strptime(req["time_after"], "%H:%M").time()
                if current_time < after_time:
                    return False
            if "time_before" in req:
                before_time = datetime.strptime(req["time_before"], "%H:%M").time()
                if current_time > before_time:
                    return False
        
        # Zero error files
        if "zero_error_files" in req:
            # TODO: Track files with zero errors
            return False
        
        return True
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for the progress dashboard display."""
        stats = self.progress_data.user_stats
        tutorials = self.progress_data.tutorial_progress
        achievements = self.progress_data.achievements
        metrics = self.progress_data.code_metrics
        
        # Calculate this week's activity
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_activity = []
        
        for i in range(7):
            date = week_start + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            day_stats = self.progress_data.daily_stats.get(date_str)
            
            week_activity.append({
                "day": date.strftime("%a"),
                "errors_fixed": day_stats.total_errors_fixed if day_stats else 0,
                "is_today": date == today
            })
        
        # Get recent achievements
        recent_achievements = []
        for aid, unlock_time in sorted(
            achievements.unlocked.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]:
            if aid in self.achievements:
                achievement = self.achievements[aid]
                recent_achievements.append({
                    "icon": achievement.icon,
                    "name": achievement.name,
                    "time_ago": self._format_time_ago(unlock_time)
                })
        
        # Calculate time saved estimate (rough: 5 min per error prevented)
        time_saved_hours = (stats.total_errors_fixed * 5) / 60
        
        return {
            "overall_stats": {
                "files_analyzed": stats.total_files_checked,
                "errors_fixed": stats.total_errors_fixed,
                "type_coverage": {
                    "start": metrics.type_coverage_start,
                    "current": metrics.type_coverage_current,
                    "improvement": metrics.type_coverage_improvement
                },
                "current_streak": stats.current_streak,
                "time_saved": time_saved_hours
            },
            "tutorial_progress": {
                "completed": len(tutorials.completed),
                "total": 10,  # TODO: Get from tutorial registry
                "percentage": (len(tutorials.completed) / 10) * 100,
                "latest": self._get_latest_tutorial(),
                "total_time": format_time_delta(tutorials.total_time_spent),
                "average_score": tutorials.average_score
            },
            "achievements": {
                "unlocked": len(achievements.unlocked),
                "total": len(self.achievements),
                "recent": recent_achievements
            },
            "week_activity": week_activity,
            "next_goals": self._get_next_goals(),
            "last_checked": self._format_time_ago(stats.last_session),
            "total_sessions": stats.total_sessions
        }
    
    def _get_latest_tutorial(self) -> Optional[Dict[str, str]]:
        """Get info about the latest tutorial activity."""
        if not self.progress_data.tutorial_progress.completed:
            return None
        
        # TODO: Get tutorial name from registry
        latest_id = self.progress_data.tutorial_progress.completed[-1]
        when = self.progress_data.tutorial_progress.last_activity
        
        return {
            "name": latest_id.replace("_", " ").title(),
            "when": self._format_time_ago(when) if when else "unknown"
        }
    
    def _get_next_goals(self) -> List[str]:
        """Get suggested next goals."""
        goals = []
        
        # Tutorial goal
        completed = len(self.progress_data.tutorial_progress.completed)
        if completed < 10:  # TODO: Get total from registry
            next_tutorial = f"Complete tutorial #{completed + 1}"
            goals.append(next_tutorial)
        
        # Error fixing goal
        if self.progress_data.user_stats.total_errors_fixed < 100:
            remaining = 100 - self.progress_data.user_stats.total_errors_fixed
            goals.append(f"Fix {remaining} more errors to reach 100")
        
        # Achievement goals
        for achievement in self.achievements.values():
            if achievement.id in self.progress_data.achievements.unlocked:
                continue
            
            # Check if close to achieving
            if "errors_fixed" in achievement.requirement:
                target = achievement.requirement["errors_fixed"]
                current = self.progress_data.user_stats.total_errors_fixed
                if current >= target * 0.8:  # 80% there
                    remaining = target - current
                    goals.append(f"Fix {remaining} more errors for '{achievement.name}'")
                    break
        
        return goals[:3]  # Top 3 goals
    
    def _format_time_ago(self, dt: datetime) -> str:
        """Format datetime as 'X time ago'."""
        if not dt:
            return "never"
        
        # Ensure dt is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
        
        now = datetime.now().astimezone()
        delta = now - dt
        
        if delta.total_seconds() < 60:
            return "just now"
        elif delta.total_seconds() < 3600:
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = delta.days
            return f"{days} day{'s' if days != 1 else ''} ago"
    
    def clear_all_progress(self) -> Dict[str, int]:
        """Clear all progress data and return what was cleared."""
        # Get counts before clearing
        cleared_info = {
            "sessions": self.progress_data.user_stats.total_sessions,
            "errors_fixed": self.progress_data.user_stats.total_errors_fixed,
            "tutorials": len(self.progress_data.tutorial_progress.completed),
            "achievements": len(self.progress_data.achievements.unlocked),
            "streak": self.progress_data.user_stats.current_streak
        }
        
        # Delete all progress files
        if self.progress_file.exists():
            self.progress_file.unlink()
        
        # Delete session files
        for session_file in self.sessions_dir.glob("*.json"):
            session_file.unlink()
        
        # Reset in-memory data
        now = datetime.now()
        self.progress_data = ProgressData(
            user_stats=UserStats(
                first_run=now,
                last_session=now
            )
        )
        
        return cleared_info