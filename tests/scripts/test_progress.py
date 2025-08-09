"""
Tests for Progress Script
==========================
Test coverage for storm_checker/scripts/progress.py
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from storm_checker.scripts.progress import (
    show_achievements, show_progress, clear_progress,
    export_progress, show_tutorials, main
)
from storm_checker.models.progress_models import Achievement, AchievementCategory


class TestShowAchievements:
    """Test the show_achievements function for complete coverage."""
    
    @patch('storm_checker.scripts.progress.print_header')
    @patch('builtins.print')
    def test_show_achievements_with_unlocked(self, mock_print, mock_print_header):
        """Test show_achievements with unlocked achievements."""
        # Create mock tracker
        tracker = Mock()
        
        # Create mock achievements
        ach1 = Mock(spec=Achievement)
        ach1.id = "first_fix"
        ach1.name = "First Fix"
        ach1.description = "Fixed your first error"
        ach1.category = AchievementCategory.BEGINNER
        ach1.icon = "🏆"
        ach1.points = 10
        ach1.secret = False
        
        ach2 = Mock(spec=Achievement)
        ach2.id = "type_master"
        ach2.name = "Type Master"
        ach2.description = "Master of types"
        ach2.category = AchievementCategory.MASTERY
        ach2.icon = "⭐"
        ach2.points = 50
        ach2.secret = False
        
        ach3 = Mock(spec=Achievement)
        ach3.id = "secret_achievement"
        ach3.name = "Secret Achievement"
        ach3.description = "Secret achievement"
        ach3.category = AchievementCategory.SPECIAL
        ach3.icon = "🎯"
        ach3.points = 100
        ach3.secret = True
        
        tracker.achievements = {
            "first_fix": ach1,
            "type_master": ach2,
            "secret_achievement": ach3
        }
        
        # Mock progress data
        progress_data = Mock()
        progress_data.achievements = Mock()
        progress_data.achievements.unlocked = {
            "first_fix": datetime(2024, 1, 1, 10, 0, 0)
        }
        progress_data.achievements.progress = {
            "type_master": {
                "percentage": 80,
                "current": 40,
                "target": 50
            }
        }
        tracker.progress_data = progress_data
        
        # Call the function
        show_achievements(tracker)
        
        # Verify header was printed
        mock_print_header.assert_called_once_with(
            "Storm-Checker Achievements",
            "Track your type safety journey"
        )
        
        # Verify achievements were displayed
        print_calls = str(mock_print.call_args_list)
        
        # Check that unlocked achievement is shown
        assert "First Fix" in print_calls
        assert "Fixed your first error" in print_calls
        assert "Unlocked: 2024-01-01" in print_calls
        
        # Check that in-progress achievement is shown with progress
        assert "Type Master" in print_calls
        assert "Progress: 40/50 (80%)" in print_calls
        
        # Check that secret achievement is shown
        assert "Secret Achievement" in print_calls
        assert "???" in print_calls  # Secret not unlocked
        
        # Check summary
        assert "Achievement Progress: 1/3 (33%)" in print_calls
        assert "Total Points: 10" in print_calls
    
    @patch('storm_checker.scripts.progress.print_header')
    @patch('builtins.print')
    def test_show_achievements_all_unlocked(self, mock_print, mock_print_header):
        """Test show_achievements with all achievements unlocked."""
        tracker = Mock()
        
        # Create achievements
        ach1 = Mock(spec=Achievement)
        ach1.id = "ach1"
        ach1.name = "Achievement 1"
        ach1.description = "Description 1"
        ach1.category = AchievementCategory.BEGINNER
        ach1.icon = "🏆"
        ach1.points = 10
        ach1.secret = False
        
        ach2 = Mock(spec=Achievement)
        ach2.id = "ach2"
        ach2.name = "Achievement 2"
        ach2.description = "Description 2"
        ach2.category = AchievementCategory.BEGINNER
        ach2.icon = "⭐"
        ach2.points = 20
        ach2.secret = False
        
        tracker.achievements = {"ach1": ach1, "ach2": ach2}
        
        # All achievements unlocked
        progress_data = Mock()
        progress_data.achievements = Mock()
        progress_data.achievements.unlocked = {
            "ach1": datetime(2024, 1, 1),
            "ach2": datetime(2024, 1, 2)
        }
        progress_data.achievements.progress = {}
        tracker.progress_data = progress_data
        
        show_achievements(tracker)
        
        print_calls = str(mock_print.call_args_list)
        
        # Check both achievements shown as unlocked
        assert "Achievement 1" in print_calls
        assert "Achievement 2" in print_calls
        assert "Unlocked: 2024-01-01" in print_calls
        assert "Unlocked: 2024-01-02" in print_calls
        
        # Check 100% completion
        assert "Achievement Progress: 2/2 (100%)" in print_calls
        assert "Total Points: 30" in print_calls
    
    @patch('storm_checker.scripts.progress.print_header')
    @patch('builtins.print')
    def test_show_achievements_no_achievements(self, mock_print, mock_print_header):
        """Test show_achievements with no achievements unlocked."""
        tracker = Mock()
        
        # Create achievement
        ach = Mock(spec=Achievement)
        ach.id = "test"
        ach.name = "Test Achievement"
        ach.description = "Test"
        ach.category = AchievementCategory.BEGINNER
        ach.icon = "🏆"
        ach.points = 10
        ach.secret = False
        
        tracker.achievements = {"test": ach}
        
        # No achievements unlocked
        progress_data = Mock()
        progress_data.achievements = Mock()
        progress_data.achievements.unlocked = {}
        progress_data.achievements.progress = {}
        tracker.progress_data = progress_data
        
        show_achievements(tracker)
        
        print_calls = str(mock_print.call_args_list)
        
        # Check achievement shown as not unlocked
        assert "Test Achievement" in print_calls
        assert "Not yet unlocked" in print_calls
        
        # Check 0% completion
        assert "Achievement Progress: 0/1 (0%)" in print_calls
        assert "Total Points: 0" in print_calls
    
    @patch('storm_checker.scripts.progress.print_header')
    @patch('builtins.print')
    def test_show_achievements_with_categories(self, mock_print, mock_print_header):
        """Test show_achievements groups by category correctly."""
        tracker = Mock()
        
        # Create achievements in different categories
        beginner_ach = Mock(spec=Achievement)
        beginner_ach.id = "beginner"
        beginner_ach.name = "Beginner Achievement"
        beginner_ach.description = "For beginners"
        beginner_ach.category = AchievementCategory.BEGINNER
        beginner_ach.icon = "🌱"
        beginner_ach.points = 5
        beginner_ach.secret = False
        
        advanced_ach = Mock(spec=Achievement)
        advanced_ach.id = "advanced"
        advanced_ach.name = "Advanced Achievement"
        advanced_ach.description = "For experts"
        advanced_ach.category = AchievementCategory.MASTERY
        advanced_ach.icon = "🚀"
        advanced_ach.points = 50
        advanced_ach.secret = False
        
        special_ach = Mock(spec=Achievement)
        special_ach.id = "special"
        special_ach.name = "Special Achievement"
        special_ach.description = "Special one"
        special_ach.category = AchievementCategory.SPECIAL
        special_ach.icon = "✨"
        special_ach.points = 100
        special_ach.secret = True
        
        tracker.achievements = {
            "beginner": beginner_ach,
            "advanced": advanced_ach,
            "special": special_ach
        }
        
        progress_data = Mock()
        progress_data.achievements = Mock()
        progress_data.achievements.unlocked = {
            "beginner": datetime(2024, 1, 1)
        }
        progress_data.achievements.progress = {}
        tracker.progress_data = progress_data
        
        show_achievements(tracker)
        
        print_calls = str(mock_print.call_args_list)
        
        # Check categories are shown
        assert "Beginner Achievements" in print_calls
        assert "Mastery Achievements" in print_calls
        assert "Special Achievements" in print_calls
        
        # Check achievements are in correct categories
        assert "Beginner Achievement" in print_calls
        assert "Advanced Achievement" in print_calls
        assert "Special Achievement" in print_calls
    
    @patch('storm_checker.scripts.progress.print_header')
    @patch('builtins.print')
    def test_show_achievements_with_progress_no_target(self, mock_print, mock_print_header):
        """Test achievement with progress but missing target field."""
        tracker = Mock()
        
        ach = Mock(spec=Achievement)
        ach.id = "test"
        ach.name = "Test"
        ach.description = "Test achievement"
        ach.category = AchievementCategory.BEGINNER
        ach.icon = "🏆"
        ach.points = 10
        ach.secret = False
        
        tracker.achievements = {"test": ach}
        
        progress_data = Mock()
        progress_data.achievements = Mock()
        progress_data.achievements.unlocked = {}
        # Progress info without all fields
        progress_data.achievements.progress = {
            "test": {
                "percentage": 50,
                "current": 5
                # Missing 'target' field
            }
        }
        tracker.progress_data = progress_data
        
        # Should handle missing target gracefully
        show_achievements(tracker)
        
        # Function should complete without error
        mock_print_header.assert_called_once()


class TestOtherProgressFunctions:
    """Test other functions in progress.py for completeness."""
    
    @patch('storm_checker.scripts.progress.ProgressDashboard')
    def test_show_progress(self, mock_dashboard_class):
        """Test show_progress function."""
        tracker = Mock()
        tracker.get_dashboard_data.return_value = {"test": "data"}
        
        mock_dashboard = Mock()
        mock_dashboard_class.return_value = mock_dashboard
        
        show_progress(tracker)
        
        mock_dashboard_class.assert_called_once()
        tracker.get_dashboard_data.assert_called_once()
        mock_dashboard.render.assert_called_once_with({"test": "data"})
    
    @patch('builtins.input', return_value='yes')
    @patch('storm_checker.scripts.progress.print_success')
    @patch('storm_checker.scripts.progress.print_warning')
    @patch('builtins.print')
    def test_clear_progress_confirmed(self, mock_print, mock_warning, mock_success, mock_input):
        """Test clear_progress with confirmation."""
        tracker = Mock()
        tracker.get_dashboard_data.return_value = {
            "overall_stats": {
                "errors_fixed": 100,
                "current_streak": 5
            },
            "tutorial_progress": {"completed": 3},
            "achievements": {"unlocked": 10},
            "total_sessions": 20
        }
        tracker.clear_all_progress.return_value = {
            "sessions": 20,
            "errors_fixed": 100
        }
        
        clear_progress(tracker)
        
        mock_warning.assert_called_once()
        mock_success.assert_called_once()
        tracker.clear_all_progress.assert_called_once()
    
    @patch('builtins.input', return_value='no')
    @patch('storm_checker.scripts.progress.print_info')
    @patch('storm_checker.scripts.progress.print_warning')
    def test_clear_progress_cancelled(self, mock_warning, mock_info, mock_input):
        """Test clear_progress when cancelled."""
        tracker = Mock()
        tracker.get_dashboard_data.return_value = {
            "overall_stats": {"errors_fixed": 0, "current_streak": 0},
            "tutorial_progress": {"completed": 0},
            "achievements": {"unlocked": 0},
            "total_sessions": 0
        }
        
        clear_progress(tracker)
        
        mock_warning.assert_called_once()
        mock_info.assert_called_once_with("Cancelled. Your progress data is safe.")
        tracker.clear_all_progress.assert_not_called()
    
    @patch('storm_checker.scripts.progress.Path')
    @patch('storm_checker.scripts.progress.print_success')
    def test_export_progress_json(self, mock_success, mock_path):
        """Test export_progress with JSON format."""
        tracker = Mock()
        tracker.get_dashboard_data.return_value = {
            "test": "data",
            "overall_stats": {
                "errors_fixed": 10,
                "current_streak": 2,
                "type_coverage": {"start": 50.0, "current": 75.0}
            },
            "tutorial_progress": {"completed": 5},
            "achievements": {"unlocked": 3},
            "total_sessions": 15
        }
        
        mock_file = Mock()
        mock_path.return_value = mock_file
        
        export_progress(tracker, format="json")
        
        mock_file.write_text.assert_called_once()
        mock_success.assert_called_once_with("✅ Progress exported to stormchecker_progress.json")
    
    @patch('storm_checker.scripts.progress.Path')
    @patch('storm_checker.scripts.progress.print_success')
    def test_export_progress_csv(self, mock_success, mock_path):
        """Test export_progress with CSV format."""
        tracker = Mock()
        tracker.get_dashboard_data.return_value = {
            "overall_stats": {
                "errors_fixed": 10,
                "current_streak": 2,
                "type_coverage": {"start": 50.0, "current": 75.0}
            },
            "tutorial_progress": {"completed": 5},
            "achievements": {"unlocked": 3},
            "total_sessions": 15
        }
        
        mock_file = Mock()
        mock_path.return_value = mock_file
        
        export_progress(tracker, format="csv")
        
        mock_file.write_text.assert_called_once()
        # Check CSV content
        csv_content = mock_file.write_text.call_args[0][0]
        assert "Metric,Value" in csv_content
        assert "Total Sessions,15" in csv_content
        assert "Errors Fixed,10" in csv_content
        mock_success.assert_called_once_with("✅ Progress exported to stormchecker_progress.csv")
    
    @patch('storm_checker.scripts.progress.print_error')
    def test_export_progress_invalid_format(self, mock_error):
        """Test export_progress with invalid format."""
        tracker = Mock()
        tracker.get_dashboard_data.return_value = {}
        
        export_progress(tracker, format="xml")
        
        mock_error.assert_called_once_with("Unsupported export format: xml")
    
    @patch('storm_checker.scripts.progress.print_info')
    @patch('storm_checker.scripts.progress.print_header')
    @patch('builtins.print')
    def test_show_tutorials_no_progress(self, mock_print, mock_header, mock_info):
        """Test show_tutorials with no tutorial progress."""
        tracker = Mock()
        tracker.progress_data = Mock()
        tracker.progress_data.tutorial_progress = Mock()
        tracker.progress_data.tutorial_progress.completed = []
        tracker.progress_data.tutorial_progress.in_progress = {}
        
        show_tutorials(tracker)
        
        mock_header.assert_called_once()
        mock_info.assert_called_once_with(
            "No tutorial progress yet. Start with 'stormcheck tutorial hello_world'!"
        )
    
    @patch('storm_checker.scripts.progress.print_header')
    @patch('builtins.print')
    def test_show_tutorials_with_progress(self, mock_print, mock_header):
        """Test show_tutorials with tutorial progress."""
        tracker = Mock()
        tracker.progress_data = Mock()
        tutorial_progress = Mock()
        tutorial_progress.completed = ["hello_world", "basic_types"]
        tutorial_progress.scores = {"hello_world": 95, "basic_types": 88}
        tutorial_progress.in_progress = {"advanced_types": {"percentage": 60}}
        tutorial_progress.total_time_spent = 3600  # 60 minutes
        tutorial_progress.average_score = 91.5
        tutorial_progress.last_activity = datetime.now()
        tracker.progress_data.tutorial_progress = tutorial_progress
        
        show_tutorials(tracker)
        
        mock_header.assert_called_once()
        print_calls = str(mock_print.call_args_list)
        
        # Check completed tutorials shown
        assert "Completed Tutorials" in print_calls
        assert "Hello World - Score: 95%" in print_calls
        assert "Basic Types - Score: 88%" in print_calls
        
        # Check in-progress tutorials shown
        assert "In Progress" in print_calls
        assert "Advanced Types - 60% complete" in print_calls
        
        # Check statistics
        assert "Total Time Learning: 60.0 minutes" in print_calls
        assert "Average Score: 91.5%" in print_calls
        assert "Last Activity: today" in print_calls