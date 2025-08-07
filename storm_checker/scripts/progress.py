#!/usr/bin/env python3
"""
Storm-Checker Progress Command
==============================
Track and display user progress, achievements, and statistics.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

try:
    # When installed via pip
    from storm_checker.cli.colors import (
        ColorPrinter, print_header, print_success, print_error,
        print_warning, print_info, THEME, RESET, BOLD
    )
    from storm_checker.logic.progress_tracker_v2 import EnhancedProgressTracker
    from storm_checker.cli.components.progress_dashboard import ProgressDashboard
except ImportError:
    # For development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from storm_checker.cli.colors import (
        ColorPrinter, print_header, print_success, print_error,
        print_warning, print_info, THEME, RESET, BOLD
    )
    from storm_checker.logic.progress_tracker_v2 import EnhancedProgressTracker
    from storm_checker.cli.components.progress_dashboard import ProgressDashboard


def show_progress(tracker: EnhancedProgressTracker) -> None:
    """Display the progress dashboard."""
    dashboard = ProgressDashboard()
    data = tracker.get_dashboard_data()
    dashboard.render(data)


def clear_progress(tracker: EnhancedProgressTracker) -> None:
    """Clear all progress data with confirmation."""
    # Get what will be cleared
    data = tracker.get_dashboard_data()
    stats = data["overall_stats"]
    tutorials = data["tutorial_progress"]
    achievements = data["achievements"]

    # Show warning
    print()
    print_warning("⚠️  WARNING: Clear All Progress Data?")
    print()
    print("This will permanently delete:")
    print(f"  • {data['total_sessions']} analysis sessions")
    print(f"  • {stats['errors_fixed']} fixed errors history")
    print(f"  • {tutorials['completed']} completed tutorials")
    print(f"  • {achievements['unlocked']} unlocked achievements")
    print(f"  • {stats['current_streak']} day streak")
    print()
    print("Your code and type annotations will NOT be affected.")
    print()

    # Get confirmation
    confirmation = input("Type 'yes' to confirm deletion: ").strip().lower()

    if confirmation == 'yes':
        cleared = tracker.clear_all_progress()
        print()
        print_success("✅ Progress data cleared successfully.")
        print("Starting fresh! Run 'stormcheck mypy' to begin tracking again.")
    else:
        print()
        print_info("Cancelled. Your progress data is safe.")


def export_progress(tracker: EnhancedProgressTracker, format: str = "json") -> None:
    """Export progress data in specified format."""
    data = tracker.get_dashboard_data()

    if format == "json":
        import json
        output = json.dumps(data, indent=2, default=str)
        filename = "stormchecker_progress.json"
    elif format == "csv":
        # Simple CSV export of key metrics
        lines = [
            "Metric,Value",
            f"Total Sessions,{data['total_sessions']}",
            f"Errors Fixed,{data['overall_stats']['errors_fixed']}",
            f"Current Streak,{data['overall_stats']['current_streak']}",
            f"Tutorials Completed,{data['tutorial_progress']['completed']}",
            f"Achievements Unlocked,{data['achievements']['unlocked']}",
            f"Type Coverage Start,{data['overall_stats']['type_coverage']['start']:.1f}%",
            f"Type Coverage Current,{data['overall_stats']['type_coverage']['current']:.1f}%",
        ]
        output = "\n".join(lines)
        filename = "stormchecker_progress.csv"
    else:
        print_error(f"Unsupported export format: {format}")
        return

    # Write to file
    output_path = Path(filename)
    output_path.write_text(output)
    print_success(f"✅ Progress exported to {filename}")


def show_achievements(tracker: EnhancedProgressTracker) -> None:
    """Display detailed achievements view."""
    data = tracker.progress_data.achievements
    all_achievements = tracker.achievements

    print_header("Storm-Checker Achievements", "Track your type safety journey")
    print()

    # Group by category
    by_category = {}
    for achievement in all_achievements.values():
        category = achievement.category.value
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(achievement)

    # Display each category
    for category, achievements in by_category.items():
        print(f"{BOLD}{category.title()} Achievements{RESET}")
        print("─" * 40)

        for achievement in achievements:
            is_unlocked = achievement.id in data.unlocked

            if is_unlocked:
                unlock_time = data.unlocked[achievement.id]
                time_str = unlock_time.strftime("%Y-%m-%d")
                print(f"{achievement.icon} {THEME['success']}{achievement.name}{RESET} - {achievement.description}")
                print(f"   {THEME['text_muted']}Unlocked: {time_str}{RESET}")
            else:
                # Show progress if available
                progress_info = data.progress.get(achievement.id)
                if progress_info:
                    pct = progress_info['percentage']
                    current = progress_info['current']
                    target = progress_info['target']
                    print(f"{THEME['text_muted']}{achievement.icon} {achievement.name} - {achievement.description}{RESET}")
                    print(f"   Progress: {current}/{target} ({pct:.0f}%)")
                else:
                    print(f"{THEME['text_muted']}{achievement.icon} {achievement.name} - {achievement.description}{RESET}")
                    if not achievement.secret:
                        print(f"   {THEME['text_muted']}Not yet unlocked{RESET}")
                    else:
                        print(f"   {THEME['text_muted']}???{RESET}")

        print()

    # Summary
    total = len(all_achievements)
    unlocked = len(data.unlocked)
    percentage = (unlocked / total * 100) if total > 0 else 0

    print(f"{BOLD}Achievement Progress: {unlocked}/{total} ({percentage:.0f}%){RESET}")

    # Calculate total points
    total_points = sum(
        all_achievements[aid].points
        for aid in data.unlocked
        if aid in all_achievements
    )
    print(f"Total Points: {total_points} 🏆")


def show_tutorials(tracker: EnhancedProgressTracker) -> None:
    """Display tutorial-specific progress."""
    tutorials = tracker.progress_data.tutorial_progress

    print_header("Tutorial Progress", "Your learning journey")
    print()

    if not tutorials.completed and not tutorials.in_progress:
        print_info("No tutorial progress yet. Start with 'stormcheck tutorial hello_world'!")
        return

    # Completed tutorials
    if tutorials.completed:
        print(f"{BOLD}Completed Tutorials{RESET}")
        print("─" * 40)
        for tutorial_id in tutorials.completed:
            score = tutorials.scores.get(tutorial_id, 0)
            name = tutorial_id.replace("_", " ").title()
            print(f"✅ {name} - Score: {score}%")
        print()

    # In progress tutorials
    if tutorials.in_progress:
        print(f"{BOLD}In Progress{RESET}")
        print("─" * 40)
        for tutorial_id, progress in tutorials.in_progress.items():
            name = tutorial_id.replace("_", " ").title()
            pct = progress.get("percentage", 0)
            print(f"📚 {name} - {pct:.0f}% complete")
        print()

    # Statistics
    print(f"{BOLD}Statistics{RESET}")
    print(f"Total Time Learning: {tutorials.total_time_spent / 60:.1f} minutes")
    print(f"Average Score: {tutorials.average_score:.1f}%")

    if tutorials.last_activity:
        from datetime import datetime
        days_ago = (datetime.now() - tutorials.last_activity).days
        if days_ago == 0:
            when = "today"
        elif days_ago == 1:
            when = "yesterday"
        else:
            when = f"{days_ago} days ago"
        print(f"Last Activity: {when}")


def main():
    """Main entry point for progress command."""
    parser = argparse.ArgumentParser(
        description="Track and display Storm-Checker progress",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  stormcheck progress              # Show progress dashboard
  stormcheck progress --clear      # Clear all progress data
  stormcheck progress --export     # Export progress to JSON
  stormcheck progress --achievements # Show detailed achievements
  stormcheck progress --tutorials  # Show tutorial progress
        """
    )

    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all progress data (with confirmation)'
    )
    parser.add_argument(
        '--export',
        choices=['json', 'csv'],
        help='Export progress data in specified format'
    )
    parser.add_argument(
        '--achievements',
        action='store_true',
        help='Show detailed achievements view'
    )
    parser.add_argument(
        '--tutorials',
        action='store_true',
        help='Show tutorial-specific progress'
    )

    args = parser.parse_args()

    # Initialize tracker
    try:
        tracker = EnhancedProgressTracker()
    except Exception as e:
        print_error(f"Failed to initialize progress tracker: {e}")
        sys.exit(1)

    # Handle commands
    try:
        if args.clear:
            clear_progress(tracker)
        elif args.export:
            export_progress(tracker, args.export)
        elif args.achievements:
            show_achievements(tracker)
        elif args.tutorials:
            show_tutorials(tracker)
        else:
            show_progress(tracker)
    except KeyboardInterrupt:
        print("\n")
        print_info("Progress check cancelled.")
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
