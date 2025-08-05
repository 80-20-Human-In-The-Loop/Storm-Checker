#!/usr/bin/env python3
"""
Hello World Tutorial - Test Tutorial for Storm-Checker
======================================================
A simple test tutorial to demonstrate the slideshow system.
"""

from typing import Dict, List, Optional
from .base_tutorial import BaseTutorial, Question


class HelloWorldTutorial(BaseTutorial):
    """Test tutorial to demonstrate the tutorial system."""
    
    @property
    def id(self) -> str:
        """Unique identifier for this tutorial."""
        return "hello_world"
    
    @property
    def title(self) -> str:
        """Display title of the tutorial."""
        return "Hello Storm-Checker! 👋"
    
    @property
    def description(self) -> str:
        """Brief description of what this tutorial covers."""
        return "Learn how to use the Storm-Checker tutorial system"
    
    @property
    def difficulty(self) -> int:
        """Difficulty level from 1-5."""
        return 1  # Easiest possible
    
    @property
    def estimated_minutes(self) -> int:
        """Estimated time to complete in minutes."""
        return 5
    
    @property
    def pages(self) -> List[str]:
        """List of tutorial pages (4 slides for testing)."""
        return [
            # Slide 1: Welcome
            """# Welcome to Storm-Checker! 🌩️

Storm-Checker is your friendly companion for learning Python type safety.

## What You'll Learn:
• How to navigate tutorials
• The importance of type hints
• How to fix common type errors
• Best practices for type-safe Python

Ready to begin your journey to type safety? Let's go!""",
            
            # Slide 2: Navigation Basics
            """# Tutorial Navigation 🧭

Here's how to navigate through tutorials:

## Keyboard Controls:
• **Enter** - Next page
• **b** - Previous page
• **q** - Quit tutorial

## Progress Tracking:
Your progress is automatically saved! If you quit and come back,
you can resume where you left off.

The progress bar at the bottom shows how far you've come.""",
            
            # Slide 3: About Questions (has mid-tutorial question)
            """# Knowledge Checks 📝

Throughout tutorials, you'll encounter questions to test your understanding.

## Important Notes:
• Questions appear after key concepts
• Multiple choice format with arrow key navigation
• Mid-tutorial questions must be answered correctly to continue
• Final questions test overall comprehension

⚠️ **Warning**: If you fail a mid-tutorial question, you'll need to restart!
This ensures you master each concept before moving forward.""",
            
            # Slide 4: Completion
            """# You're Ready! 🎉

Congratulations on completing the Hello World tutorial!

## What's Next?
1. Run `stormcheck mypy --edu` to see available tutorials
2. Start with `pyproject_setup` to configure your project
3. Work through tutorials as you encounter different error types
4. Track your progress with `stormcheck mypy --dashboard`

Remember: Type safety is a journey, not a destination.
Happy learning! 🚀"""
        ]
    
    @property
    def questions(self) -> Dict[int, Question]:
        """Questions mapped to page numbers."""
        return {
            1: Question(  # After slide 2 (Navigation) - Mid-tutorial question
                text="Which key do you press to go to the next page?",
                options=[
                    "n",
                    "Space",
                    "Enter",
                    "Right Arrow"
                ],
                correct_index=2,
                explanation="Press Enter to advance to the next page in tutorials.",
                hint="It's the most common 'confirm' key..."
            ),
            3: Question(  # After final slide - Completion question
                text="What happens if you fail a mid-tutorial question?",
                options=[
                    "Nothing, you can continue",
                    "You get a warning but can proceed",
                    "You must restart the tutorial",
                    "Your progress is reset completely"
                ],
                correct_index=2,
                explanation="Mid-tutorial questions ensure mastery of concepts. Failing one requires you to restart and review the material.",
                hint="We want to ensure you truly understand each concept..."
            )
        }
    
    @property
    def related_errors(self) -> List[str]:
        """This is just a test tutorial, no specific errors."""
        return []
    
    @property
    def practice_exercise(self) -> Optional[str]:
        """Optional practice exercise."""
        return """Try these commands to explore Storm-Checker:

1. Run `stormcheck mypy` to check your code
2. Run `stormcheck mypy --edu` for educational mode
3. Run `stormcheck mypy --dashboard` to see your progress

Explore and have fun learning!"""


# Demo function to test the tutorial
def demo():
    """Run the hello world tutorial."""
    tutorial = HelloWorldTutorial()
    tutorial.run()


if __name__ == "__main__":
    demo()