#!/usr/bin/env python3
"""
Storm-Checker MyPy Tutorial System
==================================
Interactive tutorials for mastering Python type safety with MyPy.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import json

try:
    # When installed via pip
    from storm_checker.cli.colors import (
        ColorPrinter, print_header, print_success, print_error,
        print_warning, print_info, print_learn,
        THEME, RESET, BOLD
    )
    from storm_checker.tutorials.base_tutorial import BaseTutorial
    from storm_checker.logic.progress_tracker import ProgressTracker
except ImportError:
    # For development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from storm_checker.cli.colors import (
        ColorPrinter, print_header, print_success, print_error,
        print_warning, print_info, print_learn,
        THEME, RESET, BOLD
    )
    from storm_checker.tutorials.base_tutorial import BaseTutorial
    from storm_checker.logic.progress_tracker import ProgressTracker


class MyPyTutorialRegistry:
    """Registry for MyPy-specific tutorials."""

    def __init__(self):
        self._tutorials: Dict[str, Type[BaseTutorial]] = {}
        self._load_tutorials()

    def _load_tutorials(self) -> None:
        """Load MyPy-specific tutorial modules."""
        from storm_checker.tutorials.pyproject_setup import PyprojectSetupTutorial
        from storm_checker.tutorials.type_annotations_basics import TypeAnnotationsBasics

        self._tutorials = {
            'pyproject_setup': PyprojectSetupTutorial,
            'type_annotations_basics': TypeAnnotationsBasics,
            # TODO: Add more MyPy tutorials:
            # 'optional_types': OptionalTypesTutorial,
            # 'generic_types': GenericTypesTutorial,
            # 'imports_modules': ImportsModulesTutorial,
            # 'inheritance_protocols': InheritanceProtocolsTutorial,
            # 'advanced_typing': AdvancedTypingTutorial,
        }

    def get_all(self) -> Dict[str, Type[BaseTutorial]]:
        """Get all registered MyPy tutorials."""
        return self._tutorials

    def get(self, tutorial_id: str) -> Optional[Type[BaseTutorial]]:
        """Get a specific MyPy tutorial by ID."""
        return self._tutorials.get(tutorial_id)

    def list_tutorials(self) -> List[Dict[str, Any]]:
        """Get list of MyPy tutorial info sorted by difficulty."""
        tutorials_info = []

        for tutorial_id, tutorial_class in self._tutorials.items():
            instance = tutorial_class()

            # Check if completed
            from storm_checker.logic.utils import get_data_directory
            progress_file = get_data_directory() / "tutorial_progress" / f"{tutorial_id}.json"
            is_completed = False
            if progress_file.exists():
                try:
                    with open(progress_file, 'r') as f:
                        data = json.load(f)
                        is_completed = data.get('completed', False)
                except:
                    pass

            tutorials_info.append({
                'id': tutorial_id,
                'title': instance.title,
                'description': instance.description,
                'difficulty': instance.difficulty,
                'estimated_minutes': instance.estimated_minutes,
                'completed': is_completed,
                'related_errors': instance.related_errors
            })

        # Sort by difficulty, then by title
        tutorials_info.sort(key=lambda x: (x['difficulty'], x['title']))

        return tutorials_info


def list_mypy_tutorials(registry: MyPyTutorialRegistry) -> None:
    """Display list of available MyPy tutorials with progress tracking."""
    print_header("MyPy Type Safety Tutorials", "Master Python typing step by step")

    tutorials = registry.list_tutorials()

    if not tutorials:
        print_warning("No MyPy tutorials found!")
        return

    # Calculate progress
    completed_count = sum(1 for tut in tutorials if tut['completed'])
    total_count = len(tutorials)
    progress_pct = (completed_count / total_count * 100) if total_count > 0 else 0

    # Show progress summary
    print(f"\n{BOLD}Your Progress:{RESET}")
    print(f"  {ColorPrinter.success(f'✅ Completed: {completed_count}/{total_count} tutorials ({progress_pct:.0f}%)')}")
    if completed_count < total_count:
        remaining = total_count - completed_count
        print(f"  {ColorPrinter.info(f'📚 Remaining: {remaining} tutorials to master')}")
    print()

    # Group by difficulty
    by_difficulty = {}
    for tut in tutorials:
        diff = tut['difficulty']
        if diff not in by_difficulty:
            by_difficulty[diff] = []
        by_difficulty[diff].append(tut)

    # Display tutorials by difficulty
    for difficulty in sorted(by_difficulty.keys()):
        diff_names = {1: "Beginner", 2: "Easy", 3: "Intermediate", 4: "Advanced", 5: "Expert"}
        diff_colors = {1: "success", 2: "success", 3: "warning", 4: "error", 5: "error"}

        diff_name = diff_names.get(difficulty, f"Level {difficulty}")
        diff_color = diff_colors.get(difficulty, "info")

        print(f"{getattr(ColorPrinter, diff_color)(f'{diff_name} (Level {difficulty}):', bold=True)}")

        for tut in by_difficulty[difficulty]:
            # Status indicator
            if tut['completed']:
                status = f"{THEME['success']}✅{RESET}"
                id_color = THEME['success']
            else:
                status = "  "
                id_color = THEME['primary']

            print(f"  {status} {id_color}{tut['id']:25}{RESET} - {tut['title']}")
            print(f"     {THEME['text_muted']}{tut['description']}{RESET}")
            print(f"     {THEME['info']}⏱️  ~{tut['estimated_minutes']} minutes{RESET}")

            # Show related MyPy errors
            if tut['related_errors']:
                error_list = ", ".join(tut['related_errors'][:3])
                if len(tut['related_errors']) > 3:
                    error_list += f", +{len(tut['related_errors']) - 3} more"
                print(f"     {THEME['accent']}🔧 Helps with: {error_list}{RESET}")
            print()

    print(f"\n{BOLD}Usage:{RESET}")
    print(f"  {ColorPrinter.primary('stormcheck mypy tutorial <tutorial_id>')}  - Run a specific tutorial")
    print(f"  {ColorPrinter.primary('stormcheck mypy tutorial --list')}         - Show this list")

    # Suggest next tutorial
    if completed_count < total_count:
        # Find next uncompleted tutorial
        next_tutorial = None
        for tut in tutorials:
            if not tut['completed']:
                next_tutorial = tut
                break

        if next_tutorial:
            print(f"\\n{ColorPrinter.learn('💡 Suggested Next:')} {ColorPrinter.warning(next_tutorial['id'])} - {next_tutorial['title']}")


def run_mypy_tutorial(registry: MyPyTutorialRegistry, tutorial_id: str) -> None:
    """Run a specific MyPy tutorial."""
    tutorial_class = registry.get(tutorial_id)

    if not tutorial_class:
        print_error(f"MyPy tutorial '{tutorial_id}' not found!")
        print_info("Use 'stormcheck mypy tutorial --list' to see available tutorials.")
        sys.exit(1)

    # Create and run the tutorial
    try:
        tutorial = tutorial_class()
        tutorial.run()
    except KeyboardInterrupt:
        print(f"\\n{THEME['warning']}Tutorial interrupted.{RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error running tutorial: {e}")
        sys.exit(1)


def main():
    """Main entry point for MyPy tutorial command."""
    parser = argparse.ArgumentParser(
        description="Storm-Checker MyPy Tutorial System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  stormcheck mypy tutorial --list              # List all MyPy tutorials with progress
  stormcheck mypy tutorial pyproject_setup     # Learn MyPy configuration
  stormcheck mypy tutorial type_annotations_basics  # Master type annotations
        """
    )

    parser.add_argument(
        'tutorial_id',
        nargs='?',
        help='ID of the MyPy tutorial to run'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List all available MyPy tutorials with progress'
    )

    args = parser.parse_args()

    # Create MyPy tutorial registry
    registry = MyPyTutorialRegistry()

    # Handle commands
    if args.list or not args.tutorial_id:
        list_mypy_tutorials(registry)
    else:
        run_mypy_tutorial(registry, args.tutorial_id)


if __name__ == "__main__":
    main()
