#!/usr/bin/env python3
"""
Storm-Checker Main CLI Entry Point
==================================
The main command-line interface for Storm-Checker.
"""

import sys
import argparse

try:
    # When installed via pip
    from cli.colors import ColorPrinter, print_header, THEME, RESET, BOLD
except ImportError:
    # For development
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from cli.colors import ColorPrinter, print_header, THEME, RESET, BOLD


def main():
    """Main entry point for stormcheck command."""
    parser = argparse.ArgumentParser(
        description="Storm-Checker - Learn Python typing through practice",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{BOLD}Available Commands:{RESET}
  {ColorPrinter.primary('mypy')}      Run MyPy type checker with educational features
  {ColorPrinter.primary('tutorial')}  Interactive tutorials for learning type safety

{BOLD}Examples:{RESET}
  stormcheck mypy                    # Check all Python files
  stormcheck mypy --edu              # Educational mode with tutorials
  stormcheck mypy --dashboard        # View progress dashboard
  stormcheck mypy tutorial --list    # List MyPy typing tutorials
  stormcheck tutorial --list         # List general tutorials
  stormcheck tutorial hello_world    # Start with the intro tutorial

{ColorPrinter.learn('Learn more at: https://github.com/80-20-Human-In-The-Loop/storm-checker')}
        """
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # MyPy command
    mypy_parser = subparsers.add_parser(
        'mypy',
        help='Run MyPy type checker with educational features'
    )
    
    # Tutorial command
    tutorial_parser = subparsers.add_parser(
        'tutorial',
        help='Interactive tutorials for learning type safety'
    )
    
    # Progress command
    progress_parser = subparsers.add_parser(
        'progress',
        help='Track and display your progress and achievements'
    )
    
    # Parse args to get the command
    args, remaining = parser.parse_known_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Route to appropriate script
    if args.command == 'mypy':
        # Import and run the mypy checker
        try:
            from scripts.check_mypy import main as mypy_main
        except ImportError:
            from check_mypy import main as mypy_main
        # Restore the remaining args for mypy parser
        sys.argv = ['check_mypy.py'] + remaining
        mypy_main()
    elif args.command == 'tutorial':
        # Import and run the tutorial system
        try:
            from scripts.tutorial import main as tutorial_main
        except ImportError:
            from tutorial import main as tutorial_main
        # Restore the remaining args for tutorial parser
        sys.argv = ['tutorial.py'] + remaining
        tutorial_main()
    elif args.command == 'progress':
        # Import and run the progress system
        try:
            from scripts.progress import main as progress_main
        except ImportError:
            from progress import main as progress_main
        # Restore the remaining args for progress parser
        sys.argv = ['progress.py'] + remaining
        progress_main()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()