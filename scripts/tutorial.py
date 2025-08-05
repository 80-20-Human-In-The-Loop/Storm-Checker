#!/usr/bin/env python3
"""
Storm-Checker Tutorial System
=============================
Interactive tutorials for learning Python type safety.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import importlib
import pkgutil

try:
    # When installed via pip
    from cli.colors import (
        ColorPrinter, print_header, print_success, print_error,
        print_warning, print_info, print_learn,
        THEME, RESET, BOLD
    )
    from tutorials.base_tutorial import BaseTutorial
    from logic.progress_tracker import ProgressTracker
    from logic.utils import get_data_directory
except ImportError:
    # For development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from cli.colors import (
        ColorPrinter, print_header, print_success, print_error,
        print_warning, print_info, print_learn,
        THEME, RESET, BOLD
    )
    from tutorials.base_tutorial import BaseTutorial
    from logic.progress_tracker import ProgressTracker
    from logic.utils import get_data_directory


class GeneralTutorialRegistry:
    """Registry for general Storm-Checker tutorials (non-MyPy specific)."""
    
    def __init__(self):
        self._tutorials: Dict[str, Type[BaseTutorial]] = {}
        self._load_tutorials()
        
    def _load_tutorials(self) -> None:
        """Load general tutorial modules."""
        from tutorials.hello_world import HelloWorldTutorial
        
        # Only include general tutorials (not MyPy-specific ones)
        self._tutorials = {
            'hello_world': HelloWorldTutorial,
        }
                    
    def get_all(self) -> Dict[str, Type[BaseTutorial]]:
        """Get all registered tutorials."""
        return self._tutorials
        
    def get(self, tutorial_id: str) -> Optional[Type[BaseTutorial]]:
        """Get a specific tutorial by ID."""
        return self._tutorials.get(tutorial_id)
        
    def list_tutorials(self) -> List[Dict[str, Any]]:
        """Get list of tutorial info sorted by difficulty."""
        tutorials_info = []
        
        for tutorial_id, tutorial_class in self._tutorials.items():
            instance = tutorial_class()
            
            # Check if completed
            # Use the instance's id property to match the saved filename
            actual_tutorial_id = instance.id
            progress_file = get_data_directory() / "tutorial_progress" / f"{actual_tutorial_id}.json"
            is_completed = False
            if progress_file.exists():
                try:
                    import json
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
                'is_hello_world': tutorial_id == 'hello_world'
            })
            
        # Sort: hello_world first, then by difficulty
        tutorials_info.sort(key=lambda x: (
            not x.get('is_hello_world', False),  # hello_world first
            x['difficulty'],
            x['title']
        ))
        
        return tutorials_info


def list_tutorials(registry: GeneralTutorialRegistry, interactive: bool = True) -> Optional[str]:
    """
    Display list of available tutorials.
    
    Args:
        registry: Tutorial registry
        interactive: Whether to use interactive menu (default True)
        
    Returns:
        Selected tutorial ID if interactive, None otherwise
    """
    tutorials = registry.list_tutorials()
    
    if not tutorials:
        print_warning("No tutorials found!")
        return None
        
    # Use interactive menu if available and requested
    if interactive:
        try:
            from cli.components.interactive_menu import InteractiveMenu
            
            # Create interactive menu
            menu = InteractiveMenu(
                title="🚀 Storm-Checker Tutorials",
                subtitle="Learn Python typing step by step"
            )
            
            # Set custom colors
            menu.set_custom_colors({
                'primary': '#418791',      # Teal blue
                'selection_bg': '#418791', # Teal blue
                'selection_fg': '#fff8c2', # Cream yellow
                'header': '#ccab78',       # Golden
                'normal': '#e8e8df',       # Cream
                'description': '#b3b09f',  # Soft beige
            })
            
            # Group by difficulty
            by_difficulty = {}
            for tut in tutorials:
                diff = tut['difficulty']
                if diff not in by_difficulty:
                    by_difficulty[diff] = []
                by_difficulty[diff].append(tut)
                
            # Add menu items
            for difficulty in sorted(by_difficulty.keys()):
                diff_name = ["", "Beginner", "Easy", "Intermediate", "Advanced", "Expert"][difficulty]
                diff_colors = {
                    1: '#466b5d',  # Sage green
                    2: '#466b5d',  # Sage green
                    3: '#ccab78',  # Golden
                    4: '#9c525a',  # Rose
                    5: '#9c525a',  # Rose
                }
                
                menu.add_header(f"{diff_name} (Level {difficulty})", color=diff_colors.get(difficulty, '#ccab78'))
                
                for tut in by_difficulty[difficulty]:
                    # Choose icon
                    if tut['is_hello_world']:
                        icon = "👋"
                    else:
                        icon = "📚"
                        
                    if tut['completed']:
                        icon = "✅"
                        
                    menu.add_item(
                        text=tut['title'],
                        value=tut['id'],
                        description=tut['description'],
                        icon=icon,
                        metadata={
                            'difficulty': tut['difficulty'],
                            'time': tut['estimated_minutes'],
                            'completed': tut['completed']
                        }
                    )
                    
                if difficulty < max(by_difficulty.keys()):
                    menu.add_separator()
                    
            # Add help text at bottom
            menu.add_separator()
            menu.add_header("For MyPy Type Safety Tutorials:", color='#375c69')
            print(f"\n  {ColorPrinter.learn('stormcheck mypy tutorial --list')}    - List MyPy typing tutorials")
            print(f"  {ColorPrinter.learn('stormcheck mypy tutorial <name>')}     - Run MyPy tutorial")
            
            # Run interactive menu
            selected = menu.run()
            
            if selected:
                return selected.value
            else:
                print(f"\n{THEME['warning']}No tutorial selected.{RESET}")
                return None
                
        except (ImportError, Exception) as e:
            # Fallback to non-interactive mode
            print_warning(f"Interactive menu not available: {e}")
            interactive = False
            
    # Non-interactive fallback
    if not interactive:
        print_header("Storm-Checker Tutorials", "Learn Python typing step by step")
        print(f"\n{BOLD}Available Tutorials:{RESET}\n")
        
        # Group by difficulty
        by_difficulty = {}
        for tut in tutorials:
            diff = tut['difficulty']
            if diff not in by_difficulty:
                by_difficulty[diff] = []
            by_difficulty[diff].append(tut)
            
        # Display tutorials
        for difficulty in sorted(by_difficulty.keys()):
            diff_name = ["", "Beginner", "Easy", "Intermediate", "Advanced", "Expert"][difficulty]
            diff_color = ["", "success", "success", "warning", "error", "error"][difficulty]
            
            print(f"{getattr(ColorPrinter, diff_color)(f'{diff_name} (Level {difficulty}):', bold=True)}")
            
            for tut in by_difficulty[difficulty]:
                # Status indicator
                if tut['completed']:
                    status = f"{THEME['success']}✅{RESET}"
                    id_color = THEME['success']
                else:
                    status = "  "
                    id_color = THEME['primary']
                    
                # Special marker for enhanced, hello_world or completed tutorials
                special = ""
                if tut['completed']:
                    special = f" {THEME['success']}✅ Completed{RESET}"
                elif tut.get('is_enhanced'):
                    special = f" {THEME['accent']}🚀 NEW! Enhanced tutorial with rich features{RESET}"
                elif tut['is_hello_world']:
                    special = f" {THEME['accent']}👋 Start here!{RESET}"
                    
                print(f"  {status} {id_color}{tut['id']:20}{RESET} - {tut['title']}")
                print(f"     {THEME['text_muted']}{tut['description']}{RESET}")
                print(f"     {THEME['info']}⏱️  ~{tut['estimated_minutes']} minutes{RESET}{special}")
                print()
                
        print(f"\n{BOLD}Usage:{RESET}")
        print(f"  {ColorPrinter.primary('stormcheck tutorial <tutorial_id>')}  - Run a specific tutorial")
        print(f"  {ColorPrinter.primary('stormcheck tutorial --list')}        - Show this list")
        
        # Add hint about MyPy tutorials
        print(f"\n{BOLD}For MyPy Type Safety Tutorials:{RESET}")
        print(f"  {ColorPrinter.learn('stormcheck mypy tutorial --list')}    - List MyPy typing tutorials")
        print(f"  {ColorPrinter.learn('stormcheck mypy tutorial <name>')}     - Run MyPy tutorial")
            
        print(f"\n{ColorPrinter.learn('💡 Tip:')} Start with {ColorPrinter.warning('hello_world')} to learn the tutorial system!")
        
    return None


def run_tutorial(registry: GeneralTutorialRegistry, tutorial_id: str) -> None:
    """Run a specific tutorial."""
    tutorial_class = registry.get(tutorial_id)
    
    if not tutorial_class:
        print_error(f"Tutorial '{tutorial_id}' not found!")
        print_info("Use 'stormcheck tutorial --list' to see available tutorials.")
        sys.exit(1)
        
    # Create and run the tutorial
    try:
        tutorial = tutorial_class()
        tutorial.run()
    except KeyboardInterrupt:
        print(f"\n{THEME['warning']}Tutorial interrupted.{RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error running tutorial: {e}")
        sys.exit(1)


def main():
    """Main entry point for tutorial command."""
    parser = argparse.ArgumentParser(
        description="Storm-Checker Tutorial System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  stormcheck tutorial                  # Interactive tutorial menu
  stormcheck tutorial --list           # List all available tutorials
  stormcheck tutorial hello_world      # Run the introductory tutorial
  stormcheck tutorial pyproject_setup  # Learn about pyproject.toml configuration
        """
    )
    
    parser.add_argument(
        'tutorial_id',
        nargs='?',
        help='ID of the tutorial to run'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List all available tutorials (non-interactive)'
    )
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Disable interactive menu'
    )
    
    args = parser.parse_args()
    
    # Create tutorial registry
    registry = GeneralTutorialRegistry()
    
    # Handle commands
    if args.tutorial_id:
        # Direct tutorial specified
        run_tutorial(registry, args.tutorial_id)
    else:
        # Show tutorial list/menu
        interactive = not args.no_interactive and not args.list
        selected_id = list_tutorials(registry, interactive=interactive)
        
        # If a tutorial was selected from interactive menu, run it
        if selected_id:
            run_tutorial(registry, selected_id)


if __name__ == "__main__":
    main()