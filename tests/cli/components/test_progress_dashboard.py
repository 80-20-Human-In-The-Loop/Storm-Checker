"""
Simple Comprehensive Tests for ProgressDashboard
================================================
Tests for storm_checker/cli/components/progress_dashboard.py matching actual implementation.
"""

import pytest
from unittest.mock import patch
from storm_checker.cli.components.progress_dashboard import ProgressDashboard


class TestProgressDashboard:
    """Test the ProgressDashboard class with actual data structure."""
    
    def test_initialization(self):
        """Test ProgressDashboard initialization."""
        dashboard = ProgressDashboard()
        assert isinstance(dashboard, ProgressDashboard)
        assert dashboard.width == 80
        assert dashboard.border is not None
    
    @patch('builtins.print')
    def test_render_complete_dashboard(self, mock_print):
        """Test rendering complete dashboard matching demo data structure."""
        dashboard = ProgressDashboard()
        
        # Use the exact structure from demo()
        data = {
            "overall_stats": {
                "files_analyzed": 1247,
                "errors_fixed": 523,
                "type_coverage": {
                    "start": 78.3,
                    "current": 92.1,
                    "improvement": 13.8
                },
                "current_streak": 12,
                "time_saved": 4.2
            },
            "tutorial_progress": {
                "completed": 8,
                "total": 10,
                "percentage": 80,
                "latest": {
                    "name": "Advanced Generics",
                    "when": "2 days ago"
                },
                "total_time": "2h 35m",
                "average_score": 87
            },
            "achievements": {
                "unlocked": 3,
                "total": 25,
                "recent": [
                    {"icon": "🥉", "name": "Error Crusher", "time_ago": "1 day ago"},
                    {"icon": "🎓", "name": "Tutorial Graduate", "time_ago": "3 days ago"},
                    {"icon": "🔥", "name": "Week Streak", "time_ago": "5 days ago"}
                ]
            },
            "week_activity": [
                {"day": "Mon", "errors_fixed": 45, "is_today": False},
                {"day": "Tue", "errors_fixed": 28, "is_today": False},
                {"day": "Wed", "errors_fixed": 19, "is_today": False},
                {"day": "Thu", "errors_fixed": 41, "is_today": False},
                {"day": "Fri", "errors_fixed": 8, "is_today": False},
                {"day": "Sat", "errors_fixed": 0, "is_today": False},
                {"day": "Sun", "errors_fixed": 0, "is_today": True}
            ],
            "next_goals": [
                "Complete \"Type Narrowing\" tutorial",
                "Fix remaining 23 errors in models/",
                "Unlock \"Zero Errors\" achievement (17/20 files)"
            ],
            "last_checked": "2 hours ago",
            "total_sessions": 47
        }
        
        dashboard.render(data)
        
        # Check print was called multiple times (once for each section)
        assert mock_print.call_count >= 6
        
        # Get all printed content
        printed_content = ' '.join(str(call) for call in mock_print.call_args_list)
        
        # Verify key sections are rendered
        assert 'STORM-CHECKER PROGRESS' in printed_content
        assert 'Overall Statistics' in printed_content
        assert 'Tutorial Progress' in printed_content
        assert 'Recent Achievements' in printed_content
        assert "This Week's Activity" in printed_content
        assert 'Next Goals' in printed_content
        assert 'Last checked: 2 hours ago' in printed_content
        assert 'Total sessions: 47' in printed_content
    
    def test_render_header(self):
        """Test header rendering."""
        dashboard = ProgressDashboard()
        result = dashboard._render_header()
        
        assert 'STORM-CHECKER PROGRESS' in result
        assert '═' in result  # Border character
        assert dashboard.border.top(dashboard.width) in result
    
    def test_render_overall_stats_with_improvement(self):
        """Test overall statistics rendering with improvement."""
        dashboard = ProgressDashboard()
        
        stats = {
            "files_analyzed": 1000,
            "errors_fixed": 250,
            "type_coverage": {
                "start": 40.0,
                "current": 75.5,
                "improvement": 35.5
            },
            "current_streak": 5,
            "time_saved": 8.3
        }
        
        result = dashboard._render_overall_stats(stats)
        
        assert 'Overall Statistics' in result
        assert '1,000 files' in result
        assert '250 errors' in result
        assert '40.0% → 75.5%' in result
        assert '+35.5%' in result
        assert '5 days' in result
        assert '~8.3 hours' in result
    
    def test_render_overall_stats_no_improvement(self):
        """Test overall stats when there's no improvement."""
        dashboard = ProgressDashboard()
        
        stats = {
            "files_analyzed": 100,
            "errors_fixed": 0,
            "type_coverage": {
                "start": 50.0,
                "current": 50.0,
                "improvement": 0
            },
            "current_streak": 0,
            "time_saved": 0
        }
        
        result = dashboard._render_overall_stats(stats)
        
        assert '50.0% → 50.0%' in result
        # When improvement is 0, it shouldn't show the +0.0% part
    
    def test_render_tutorial_progress_with_latest(self):
        """Test tutorial progress rendering with latest tutorial."""
        dashboard = ProgressDashboard()
        
        tutorials = {
            "completed": 3,
            "total": 10,
            "percentage": 30,
            "latest": {
                "name": "Type Basics",
                "when": "yesterday"
            },
            "total_time": "5h 30m",
            "average_score": 85
        }
        
        result = dashboard._render_tutorial_progress(tutorials)
        
        assert 'Tutorial Progress' in result
        assert '30%' in result
        assert '3/10 completed' in result
        assert 'Type Basics' in result
        assert 'completed yesterday' in result
        assert '5h 30m' in result  # Total time is shown
        assert '85%' in result  # Average score is shown
    
    def test_render_tutorial_progress_no_latest(self):
        """Test tutorial progress with no latest tutorial."""
        dashboard = ProgressDashboard()
        
        tutorials = {
            "completed": 0,
            "total": 10,
            "percentage": 0,
            "latest": None,
            "total_time": "0h 0m",
            "average_score": 0
        }
        
        result = dashboard._render_tutorial_progress(tutorials)
        
        assert '0%' in result
        assert '0/10 completed' in result
        assert '0h 0m' in result  # Total time shown
        assert '0%' in result  # Average score shown
    
    def test_render_achievements_with_recent(self):
        """Test achievements rendering with recent achievements."""
        dashboard = ProgressDashboard()
        
        achievements = {
            "unlocked": 8,
            "total": 20,
            "recent": [
                {"name": "First Fix", "icon": "🏆", "time_ago": "2 days ago"},
                {"name": "Week Warrior", "icon": "💪", "time_ago": "1 day ago"}
            ]
        }
        
        result = dashboard._render_achievements(achievements)
        
        assert 'Recent Achievements' in result
        assert '8/20 unlocked' in result
        assert 'First Fix' in result  # Achievement name shown
        assert '2 days ago' in result
        assert 'Week Warrior' in result  # Achievement name shown
        assert '1 day ago' in result
    
    def test_render_achievements_empty(self):
        """Test achievements with no recent achievements."""
        dashboard = ProgressDashboard()
        
        achievements = {
            "unlocked": 0,
            "total": 20,
            "recent": []
        }
        
        result = dashboard._render_achievements(achievements)
        
        assert 'Recent Achievements' in result
        assert '0/20 unlocked' in result
        assert 'Keep going' in result or 'unlock achievements' in result  # Encouragement message
    
    def test_render_week_activity_with_data(self):
        """Test week activity rendering with activity data."""
        dashboard = ProgressDashboard()
        
        week_activity = [
            {"day": "Mon", "errors_fixed": 25, "is_today": False},
            {"day": "Tue", "errors_fixed": 30, "is_today": False},
            {"day": "Wed", "errors_fixed": 0, "is_today": False},
            {"day": "Thu", "errors_fixed": 15, "is_today": False},
            {"day": "Fri", "errors_fixed": 20, "is_today": False},
            {"day": "Sat", "errors_fixed": 5, "is_today": False},
            {"day": "Sun", "errors_fixed": 0, "is_today": True}
        ]
        
        result = dashboard._render_week_activity(week_activity)
        
        assert "This Week's Activity" in result
        assert 'Mon' in result
        assert '25 errors fixed' in result
        assert 'Sun' in result
        assert 'Today' in result
        assert '█' in result  # Activity bars
    
    def test_render_week_activity_no_activity(self):
        """Test week activity with no activity."""
        dashboard = ProgressDashboard()
        
        week_activity = [
            {"day": "Mon", "errors_fixed": 0, "is_today": False},
            {"day": "Tue", "errors_fixed": 0, "is_today": False},
            {"day": "Wed", "errors_fixed": 0, "is_today": False},
            {"day": "Thu", "errors_fixed": 0, "is_today": False},
            {"day": "Fri", "errors_fixed": 0, "is_today": False},
            {"day": "Sat", "errors_fixed": 0, "is_today": False},
            {"day": "Sun", "errors_fixed": 0, "is_today": True}
        ]
        
        result = dashboard._render_week_activity(week_activity)
        
        assert "This Week's Activity" in result
        # All days should show minimal or no activity
        assert result.count('-') >= 6  # Days with no activity show '-'
    
    def test_render_next_goals_with_goals(self):
        """Test next goals rendering with goals."""
        dashboard = ProgressDashboard()
        
        goals = [
            "Complete tutorial X",
            "Fix 100 errors",
            "Reach 90% coverage"
        ]
        
        result = dashboard._render_next_goals(goals)
        
        assert 'Next Goals' in result
        assert 'Complete tutorial X' in result
        assert 'Fix 100 errors' in result
        assert 'Reach 90% coverage' in result
    
    def test_render_next_goals_empty(self):
        """Test next goals with no goals."""
        dashboard = ProgressDashboard()
        
        goals = []
        
        result = dashboard._render_next_goals(goals)
        
        assert 'Next Goals' in result
        assert 'Keep up the great work!' in result
    
    def test_render_footer(self):
        """Test footer rendering."""
        dashboard = ProgressDashboard()
        
        data = {
            "last_checked": "2 hours ago",
            "total_sessions": 25
        }
        
        result = dashboard._render_footer(data)
        
        assert 'Last checked: 2 hours ago' in result
        assert 'Total sessions: 25' in result
    
    @patch('builtins.print')
    def test_render_with_minimal_data(self, mock_print):
        """Test rendering with minimal required data."""
        dashboard = ProgressDashboard()
        
        # Minimal data structure with all required fields
        data = {
            "overall_stats": {
                "files_analyzed": 0,
                "errors_fixed": 0,
                "type_coverage": {"start": 0, "current": 0, "improvement": 0},
                "current_streak": 0,
                "time_saved": 0
            },
            "tutorial_progress": {
                "completed": 0, "total": 1, "percentage": 0,
                "latest": None, "total_time": "0h", "average_score": 0
            },
            "achievements": {
                "unlocked": 0, "total": 1,
                "recent": []
            },
            "week_activity": [],
            "next_goals": [],
            "last_checked": "just now",
            "total_sessions": 0
        }
        
        # Should not raise any errors
        dashboard.render(data)
        assert mock_print.call_count >= 6
    
    @patch('builtins.print')
    def test_render_week_activity_empty_list(self, mock_print):
        """Test render with empty week_activity list."""
        dashboard = ProgressDashboard()
        
        data = {
            "overall_stats": {
                "files_analyzed": 10,
                "errors_fixed": 5,
                "type_coverage": {"start": 0, "current": 10, "improvement": 10},
                "current_streak": 1,
                "time_saved": 0.5
            },
            "tutorial_progress": {
                "completed": 1, "total": 5, "percentage": 20,
                "latest": None, "total_time": "0.5h", "average_score": 75
            },
            "achievements": {
                "unlocked": 1, "total": 10,
                "recent": []
            },
            "week_activity": [],  # Empty list edge case
            "next_goals": [],
            "last_checked": "now",
            "total_sessions": 1
        }
        
        # Should handle empty week_activity gracefully
        dashboard.render(data)
        assert mock_print.call_count >= 6