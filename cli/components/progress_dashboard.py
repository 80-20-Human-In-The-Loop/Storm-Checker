#!/usr/bin/env python3
"""
Progress Dashboard Display Component
====================================
Beautiful terminal display for Storm-Checker progress tracking.
"""

from typing import Dict, List, Any
import sys
from pathlib import Path

# Add parent directory to imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.colors import THEME, RESET, BOLD
from cli.components.border import Border, BorderStyle


class ProgressDashboard:
    """Render progress dashboard with beautiful formatting."""
    
    def __init__(self):
        """Initialize dashboard renderer."""
        self.border = Border(
            style=BorderStyle.DOUBLE, 
            color="primary", 
            bold=True,
            show_left=False,
            show_right=False
        )
        self.width = 80  # Fixed width for consistent display
        
    def render(self, data: Dict[str, Any]) -> None:
        """Render the complete progress dashboard."""
        print(self._render_header())
        print(self._render_overall_stats(data["overall_stats"]))
        print(self._render_tutorial_progress(data["tutorial_progress"]))
        print(self._render_achievements(data["achievements"]))
        print(self._render_week_activity(data["week_activity"]))
        print(self._render_next_goals(data["next_goals"]))
        print(self._render_footer(data))
    
    def _render_header(self) -> str:
        """Render dashboard header."""
        lines = []
        lines.append(self.border.top(self.width))
        lines.append(self.border.middle(
            self.width,
            center_text=f"{BOLD}STORM-CHECKER PROGRESS{RESET}"
        ))
        lines.append(self.border.horizontal_divider(self.width))
        return "\n".join(lines)
    
    def _render_overall_stats(self, stats: Dict[str, Any]) -> str:
        """Render overall statistics section."""
        lines = []
        lines.append(self.border.empty_line(self.width))
        lines.append(self.border.middle(
            self.width,
            left_text=f"{THEME['primary']}📊 Overall Statistics{RESET}"
        ))
        
        # Format type coverage
        coverage = stats["type_coverage"]
        coverage_text = f"{coverage['start']:.1f}% → {coverage['current']:.1f}%"
        if coverage['improvement'] > 0:
            coverage_text += f" ({THEME['success']}+{coverage['improvement']:.1f}%{RESET})"
        
        # Stats with tree structure
        stats_lines = [
            f"├─ Files Analyzed:     {THEME['info']}{stats['files_analyzed']:,} files{RESET}",
            f"├─ Errors Fixed:       {THEME['success']}{stats['errors_fixed']:,} errors{RESET}",
            f"├─ Type Coverage:      {coverage_text}",
            f"├─ Current Streak:     {THEME['warning']}{stats['current_streak']} days{RESET} 🔥",
            f"└─ Time Saved:         {THEME['accent']}~{stats['time_saved']:.1f} hours{RESET}"
        ]
        
        for line in stats_lines:
            lines.append(self.border.middle(self.width, left_text=f"{line}"))
        
        return "\n".join(lines)
    
    def _render_tutorial_progress(self, tutorials: Dict[str, Any]) -> str:
        """Render tutorial progress section."""
        lines = []
        lines.append(self.border.empty_line(self.width))
        
        # Progress bar
        completed = tutorials["completed"]
        total = tutorials["total"]
        percentage = tutorials["percentage"]
        
        bar_width = 10
        filled = int(bar_width * percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        title = f"{THEME['learn']}📚 Tutorial Progress{RESET} [{bar}] {percentage:.0f}% ({completed}/{total} completed)"
        lines.append(self.border.middle(self.width, left_text=title))
        
        # Details
        if tutorials["latest"]:
            latest = tutorials["latest"]
            lines.append(self.border.middle(
                self.width,
                left_text=f"├─ Latest: {THEME['info']}\"{latest['name']}\"{RESET} (completed {latest['when']})"
            ))
        
        lines.append(self.border.middle(
            self.width,
            left_text=f"├─ Total Learning Time: {THEME['accent']}{tutorials['total_time']}{RESET}"
        ))
        lines.append(self.border.middle(
            self.width,
            left_text=f"└─ Average Score: {THEME['success']}{tutorials['average_score']:.0f}%{RESET}"
        ))
        
        return "\n".join(lines)
    
    def _render_achievements(self, achievements: Dict[str, Any]) -> str:
        """Render achievements section."""
        lines = []
        lines.append(self.border.empty_line(self.width))
        
        unlocked = achievements["unlocked"]
        total = achievements["total"]
        
        title = f"{THEME['warning']}🏆 Recent Achievements{RESET} ({unlocked}/{total} unlocked)"
        lines.append(self.border.middle(self.width, left_text=title))
        
        # Recent achievements
        for i, achievement in enumerate(achievements["recent"]):
            if i < len(achievements["recent"]) - 1:
                prefix = "├─"
            else:
                prefix = "└─"
            
            lines.append(self.border.middle(
                self.width,
                left_text=f"{prefix} {achievement['icon']} {THEME['success']}{achievement['name']}{RESET} ({achievement['time_ago']})"
            ))
        
        # If no achievements yet
        if not achievements["recent"]:
            lines.append(self.border.middle(
                self.width,
                left_text=f"└─ {THEME['text_muted']}Keep going to unlock achievements!{RESET}"
            ))
        
        return "\n".join(lines)
    
    def _render_week_activity(self, week_activity: List[Dict[str, Any]]) -> str:
        """Render this week's activity chart."""
        lines = []
        lines.append(self.border.empty_line(self.width))
        lines.append(self.border.middle(
            self.width,
            left_text=f"{THEME['info']}📈 This Week's Activity{RESET}"
        ))
        
        # Find max for scaling
        max_errors = max(day["errors_fixed"] for day in week_activity)
        max_errors = max(max_errors, 1)  # Avoid division by zero
        
        # Render each day
        for day_data in week_activity:
            day = day_data["day"]
            errors = day_data["errors_fixed"]
            is_today = day_data["is_today"]
            
            # Create bar
            bar_max_width = 20
            bar_width = int((errors / max_errors) * bar_max_width) if errors > 0 else 0
            bar = "█" * bar_width + "░" * (bar_max_width - bar_width)
            
            # Format day
            if is_today:
                day_text = f"{THEME['warning']}{day}{RESET}"
                suffix = " Today"
            else:
                day_text = day
                suffix = ""
            
            # Format errors count
            if errors > 0:
                count_text = f"{errors} errors fixed"
            else:
                count_text = "-"
            
            line = f"{day_text} [{bar}] {count_text}{suffix}"
            lines.append(self.border.middle(self.width, left_text=line))
        
        return "\n".join(lines)
    
    def _render_next_goals(self, goals: List[str]) -> str:
        """Render next goals section."""
        lines = []
        lines.append(self.border.empty_line(self.width))
        lines.append(self.border.middle(
            self.width,
            left_text=f"{THEME['accent']}💡 Next Goals{RESET}"
        ))
        
        for i, goal in enumerate(goals):
            if i < len(goals) - 1:
                prefix = "•"
            else:
                prefix = "•"
            
            lines.append(self.border.middle(
                self.width,
                left_text=f"{prefix} {goal}"
            ))
        
        if not goals:
            lines.append(self.border.middle(
                self.width,
                left_text=f"• {THEME['text_muted']}Keep up the great work!{RESET}"
            ))
        
        return "\n".join(lines)
    
    def _render_footer(self, data: Dict[str, Any]) -> str:
        """Render dashboard footer."""
        lines = []
        lines.append(self.border.empty_line(self.width))
        lines.append(self.border.horizontal_divider(self.width))
        
        footer_text = f"Last checked: {data['last_checked']} | Total sessions: {data['total_sessions']}"
        lines.append(self.border.middle(
            self.width,
            center_text=f"{THEME['text_muted']}{footer_text}{RESET}"
        ))
        lines.append(self.border.bottom(self.width))
        
        return "\n".join(lines)


def demo():
    """Demo the progress dashboard."""
    # Sample data
    demo_data = {
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
    
    dashboard = ProgressDashboard()
    dashboard.render(demo_data)


if __name__ == "__main__":
    demo()