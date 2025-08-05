#!/usr/bin/env python3
"""
Interactive Menu Component
==========================
Beautiful interactive menu with keyboard navigation for tutorial selection.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.components.keyboard_handler import KeyboardHandler, KeyPress
from cli.components.rich_terminal import RichTerminal
from cli.components.buffered_renderer import BufferedRenderer, RenderMode


class MenuItemType(Enum):
    """Types of menu items."""
    NORMAL = "normal"
    HEADER = "header"
    SEPARATOR = "separator"


@dataclass
class MenuItem:
    """Represents a single menu item."""
    text: str
    value: Optional[str] = None
    type: MenuItemType = MenuItemType.NORMAL
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class InteractiveMenu:
    """
    Interactive menu with arrow key navigation and rich formatting.
    Uses persistent output to maintain terminal history.
    """
    
    def __init__(
        self,
        title: str = "Menu",
        subtitle: Optional[str] = None,
        use_rich: bool = True,
        persistent_mode: bool = True
    ):
        """
        Initialize interactive menu.
        
        Args:
            title: Menu title
            subtitle: Optional subtitle
            use_rich: Whether to use Rich formatting
            persistent_mode: Whether to use persistent output
        """
        self.title = title
        self.subtitle = subtitle
        self.items: List[MenuItem] = []
        self.selected_index = 0
        self.keyboard_handler = KeyboardHandler()
        self.rich_terminal = RichTerminal(use_rich=use_rich)
        self.buffered_renderer = BufferedRenderer()
        self.on_select: Optional[Callable[[MenuItem], None]] = None
        self.show_instructions = True
        self.custom_colors = {}
        
    def add_item(
        self,
        text: str,
        value: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a normal menu item."""
        self.items.append(MenuItem(
            text=text,
            value=value or text,
            type=MenuItemType.NORMAL,
            description=description,
            metadata=metadata or {},
            icon=icon,
            color=color
        ))
        
    def add_header(self, text: str, color: Optional[str] = None) -> None:
        """Add a header item (not selectable)."""
        self.items.append(MenuItem(
            text=text,
            type=MenuItemType.HEADER,
            color=color
        ))
        
    def add_separator(self) -> None:
        """Add a separator line."""
        self.items.append(MenuItem(
            text="",
            type=MenuItemType.SEPARATOR
        ))
        
    def set_custom_colors(self, colors: Dict[str, str]) -> None:
        """Set custom color mappings."""
        self.custom_colors = colors
        
    def _get_selectable_indices(self) -> List[int]:
        """Get list of selectable item indices."""
        return [
            i for i, item in enumerate(self.items)
            if item.type == MenuItemType.NORMAL
        ]
        
    def _move_selection(self, direction: int) -> None:
        """Move selection up or down."""
        selectable = self._get_selectable_indices()
        if not selectable:
            return
            
        # Find current position in selectable items
        try:
            current_pos = selectable.index(self.selected_index)
        except ValueError:
            # Current selection is not selectable, find nearest
            self.selected_index = selectable[0]
            return
            
        # Move to next/previous selectable item
        new_pos = current_pos + direction
        if 0 <= new_pos < len(selectable):
            self.selected_index = selectable[new_pos]
            
    def _render_menu(self) -> str:
        """Render the current menu state."""
        lines = []
        
        # Title section
        if self.title:
            self.rich_terminal.print_panel(
                self.title + (f"\n[dim]{self.subtitle}[/dim]" if self.subtitle else ""),
                title="Tutorial Selection",
                border_style=self.custom_colors.get('primary', 'blue')
            )
            lines.append(self.buffered_renderer.get_buffer())
            self.buffered_renderer.clear()
            
        # Menu items
        for i, item in enumerate(self.items):
            if item.type == MenuItemType.SEPARATOR:
                lines.append(f"{'─' * 60}")
                continue
                
            if item.type == MenuItemType.HEADER:
                color = item.color or self.custom_colors.get('header', 'yellow')
                lines.append(f"\n[bold {color}]{item.text}[/bold {color}]")
                continue
                
            # Normal item
            is_selected = i == self.selected_index
            
            # Build item text
            item_text = ""
            if item.icon:
                item_text += f"{item.icon} "
                
            item_text += item.text
            
            # Add metadata badges
            if item.metadata:
                if item.metadata.get('completed'):
                    item_text += f" [green]✅[/green]"
                if item.metadata.get('difficulty'):
                    diff = item.metadata['difficulty']
                    diff_colors = ['', 'green', 'green', 'yellow', 'red', 'red']
                    diff_color = diff_colors[min(diff, 5)]
                    item_text += f" [dim {diff_color}]Level {diff}[/dim {diff_color}]"
                if item.metadata.get('time'):
                    item_text += f" [dim]~{item.metadata['time']} min[/dim]"
                    
            # Selection indicator and coloring
            if is_selected:
                # Use custom selection color
                bg_color = self.custom_colors.get('selection_bg', '#418791')
                fg_color = self.custom_colors.get('selection_fg', 'white')
                lines.append(f"[{fg_color} on {bg_color}] ▶ {item_text} [/{fg_color} on {bg_color}]")
                
                # Show description if selected
                if item.description:
                    desc_color = self.custom_colors.get('description', 'dim')
                    lines.append(f"[{desc_color}]    {item.description}[/{desc_color}]")
            else:
                color = item.color or self.custom_colors.get('normal', 'white')
                lines.append(f"[{color}]   {item_text}[/{color}]")
                
        # Instructions
        if self.show_instructions:
            lines.append("")
            lines.append("[dim]Navigate with ↑↓ arrows • Select with Enter • Exit with q/Esc[/dim]")
            
        # Render all lines
        output = "\n".join(lines)
        if self.rich_terminal.use_rich:
            self.rich_terminal.print(output, markup=True)
        else:
            # Fallback without rich
            clean_output = self._strip_markup(output)
            print(clean_output)
            
        return self.buffered_renderer.get_buffer()
        
    def _strip_markup(self, text: str) -> str:
        """Remove Rich markup for fallback mode."""
        import re
        # Simple regex to remove [xxx] tags
        return re.sub(r'\[.*?\]', '', text)
        
    def run(self) -> Optional[MenuItem]:
        """
        Run the interactive menu and return selected item.
        
        Returns:
            Selected MenuItem or None if cancelled
        """
        # Ensure we have at least one selectable item
        selectable = self._get_selectable_indices()
        if not selectable:
            self.rich_terminal.print("[red]No selectable items in menu![/red]", markup=True)
            return None
            
        # Set initial selection to first selectable item
        self.selected_index = selectable[0]
        
        # Initial render
        self._render_menu()
        
        # Keyboard loop
        with self.keyboard_handler.create_input_loop() as loop:
            while loop.running:
                key_press = loop.run()
                
                if not key_press:
                    continue
                    
                # Handle navigation
                if key_press.key.value == "UP":
                    self._move_selection(-1)
                    self.buffered_renderer.clear()
                    self._render_menu()
                    
                elif key_press.key.value == "DOWN":
                    self._move_selection(1)
                    self.buffered_renderer.clear()
                    self._render_menu()
                    
                elif key_press.key.value == "ENTER":
                    selected_item = self.items[self.selected_index]
                    if selected_item.type == MenuItemType.NORMAL:
                        if self.on_select:
                            self.on_select(selected_item)
                        return selected_item
                        
                elif key_press.char in ['q', 'Q'] or key_press.key.value == "ESCAPE":
                    return None
                    
        return None
        
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.rich_terminal.cleanup()
        
    def __enter__(self):
        """Context manager support."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.cleanup()


def demo_interactive_menu():
    """Demonstrate the interactive menu component."""
    from cli.colors import print_rich_header
    
    print_rich_header("Interactive Menu Demo", "Navigate with arrow keys!")
    
    # Create menu with custom colors
    menu = InteractiveMenu(
        title="🚀 Storm-Checker Tutorials",
        subtitle="Learn Python type safety step by step"
    )
    
    # Set custom colors from the provided palette
    menu.set_custom_colors({
        'primary': '#418791',      # Teal blue
        'selection_bg': '#418791', # Teal blue
        'selection_fg': '#fff8c2', # Cream yellow
        'header': '#ccab78',       # Golden
        'normal': '#e8e8df',       # Cream
        'description': '#b3b09f',  # Soft beige
    })
    
    # Add items
    menu.add_header("Beginner Tutorials", color='#466b5d')
    
    menu.add_item(
        "Hello World",
        value="hello_world",
        description="Learn how to use the Storm-Checker tutorial system",
        icon="👋",
        metadata={'difficulty': 1, 'time': 5, 'completed': False}
    )
    
    menu.add_item(
        "Type Annotations Basics",
        value="type_basics",
        description="Introduction to Python type hints and annotations",
        icon="📝",
        metadata={'difficulty': 2, 'time': 15, 'completed': True}
    )
    
    menu.add_separator()
    menu.add_header("Intermediate Tutorials", color='#ccab78')
    
    menu.add_item(
        "Generic Types",
        value="generics",
        description="Learn about TypeVar, Generic classes, and protocols",
        icon="🔧",
        metadata={'difficulty': 3, 'time': 20, 'completed': False}
    )
    
    menu.add_item(
        "Advanced Patterns",
        value="advanced",
        description="Complex typing patterns and best practices",
        icon="🎯",
        metadata={'difficulty': 4, 'time': 30, 'completed': False}
    )
    
    # Run menu
    selected = menu.run()
    
    if selected:
        print(f"\n[green]You selected: {selected.text} (value: {selected.value})[/green]")
    else:
        print("\n[yellow]Menu cancelled[/yellow]")
        

if __name__ == "__main__":
    demo_interactive_menu()