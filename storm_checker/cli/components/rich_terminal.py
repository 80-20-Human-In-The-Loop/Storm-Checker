#!/usr/bin/env python3
"""
Rich Terminal Integration
=========================
World-class terminal capabilities using Rich library with our BufferedRenderer.
"""

import sys
from typing import Any, Optional, Union, List, Dict
from contextlib import contextmanager

try:
    from rich.console import Console, ConsoleOptions, RenderResult
    from rich.text import Text
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.rule import Rule
    from rich.prompt import Prompt, Confirm
    from rich.align import Align
    from rich.padding import Padding
    from rich.columns import Columns
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from storm_checker.cli.components.buffered_renderer import BufferedRenderer, RenderMode
from storm_checker.cli.colors import THEME, RESET


class RichTerminal:
    """
    Enhanced terminal using Rich library with BufferedRenderer integration.
    
    Provides world-class terminal features while maintaining persistent history.
    """
    
    def __init__(
        self,
        use_rich: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
        theme: Optional[str] = None
    ):
        """
        Initialize Rich terminal.
        
        Args:
            use_rich: Whether to use Rich features (falls back gracefully)
            width: Terminal width override
            height: Terminal height override  
            theme: Rich theme name
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        self.buffered_renderer = BufferedRenderer()
        
        if self.use_rich:
            self.console = Console(
                width=width,
                height=height,
                force_terminal=True,
                color_system="truecolor",
                theme=theme
            )
        else:
            self.console = None
            
        # Track current live display
        self._live_context: Optional[Live] = None
        
    def print(
        self,
        *objects: Any,
        style: Optional[str] = None,
        highlight: bool = True,
        markup: bool = True,
        emoji: bool = True,
        persist: bool = True
    ) -> None:
        """
        Print objects with Rich formatting.
        
        Args:
            objects: Objects to print
            style: Rich style string
            highlight: Whether to highlight syntax
            markup: Whether to process Rich markup
            emoji: Whether to process emoji codes
            persist: Whether to add to persistent terminal history
        """
        if self.use_rich and self.console:
            # Capture rich output to string
            with self.console.capture() as capture:
                self.console.print(
                    *objects,
                    style=style,
                    highlight=highlight,
                    markup=markup,
                    emoji=emoji
                )
            
            if persist:
                # Add to persistent history via buffered renderer
                lines = capture.get().splitlines()
                self.buffered_renderer.render_frame(lines, RenderMode.APPEND)
            else:
                # Print directly (won't persist in history)
                print(capture.get(), end='')
        else:
            # Fallback to regular print
            message = ' '.join(str(obj) for obj in objects)
            if persist:
                self.buffered_renderer.render_persistent_message(message)
            else:
                print(message)
                
    def print_panel(
        self,
        content: Any,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        style: str = "default",
        border_style: str = "blue",
        expand: bool = True,
        persist: bool = True
    ) -> None:
        """Print content in a beautiful panel."""
        if self.use_rich and self.console:
            panel = Panel(
                content,
                title=title,
                subtitle=subtitle,
                style=style,
                border_style=border_style,
                expand=expand
            )
            self.print(panel, persist=persist)
        else:
            # Fallback panel using our existing border system
            if title:
                self.print(f"=== {title} ===", persist=persist)
            self.print(str(content), persist=persist)
            if subtitle:
                self.print(f"--- {subtitle} ---", persist=persist)
                
    def print_table(
        self,
        data: List[List[str]],
        headers: Optional[List[str]] = None,
        title: Optional[str] = None,
        style: str = "default",
        persist: bool = True
    ) -> None:
        """Print data in a beautiful table."""
        if self.use_rich and self.console:
            table = Table(title=title, style=style)
            
            # Add columns
            if headers:
                for header in headers:
                    table.add_column(header, style="bold")
            else:
                # Auto-generate column headers
                if data:
                    for i in range(len(data[0])):
                        table.add_column(f"Col {i+1}")
                        
            # Add rows
            for row in data:
                table.add_row(*[str(cell) for cell in row])
                
            self.print(table, persist=persist)
        else:
            # Fallback table
            if title:
                self.print(title, persist=persist)
            if headers:
                self.print(" | ".join(headers), persist=persist)
                self.print("-" * (len(" | ".join(headers))), persist=persist)
            for row in data:
                self.print(" | ".join(str(cell) for cell in row), persist=persist)
                
    def print_markdown(
        self,
        markdown_content: str,
        style: str = "default",
        persist: bool = True
    ) -> None:
        """Print markdown content with rich formatting."""
        if self.use_rich and self.console:
            md = Markdown(markdown_content, style=style)
            self.print(md, persist=persist)
        else:
            # Simple markdown fallback
            lines = markdown_content.split('\n')
            for line in lines:
                if line.startswith('# '):
                    self.print(f"{THEME['primary']}{line[2:]}{RESET}", persist=persist)
                elif line.startswith('## '):
                    self.print(f"{THEME['learn']}{line[3:]}{RESET}", persist=persist)
                elif line.startswith('- '):
                    self.print(f"  • {line[2:]}", persist=persist)
                else:
                    self.print(line, persist=persist)
                    
    def print_code(
        self,
        code: str,
        language: str = "python",
        theme: str = "monokai",
        line_numbers: bool = False,
        persist: bool = True
    ) -> None:
        """Print syntax-highlighted code."""
        if self.use_rich and self.console:
            syntax = Syntax(
                code,
                language,
                theme=theme,
                line_numbers=line_numbers
            )
            self.print(syntax, persist=persist)
        else:
            # Fallback code display
            self.print(f"{THEME['text_muted']}```{language}{RESET}", persist=persist)
            for line in code.split('\n'):
                self.print(f"{THEME['info']}{line}{RESET}", persist=persist)
            self.print(f"{THEME['text_muted']}```{RESET}", persist=persist)
            
    def print_rule(
        self,
        title: Optional[str] = None,
        style: str = "default",
        persist: bool = True
    ) -> None:
        """Print a horizontal rule."""
        if self.use_rich and self.console:
            rule = Rule(title=title, style=style)
            self.print(rule, persist=persist)
        else:
            # Fallback rule
            width = self.buffered_renderer.terminal_width
            if title:
                rule_text = f" {title} ".center(width, '─')
            else:
                rule_text = '─' * width
            self.print(f"{THEME['text_muted']}{rule_text}{RESET}", persist=persist)
            
    def print_tree(
        self,
        data: Dict[str, Any],
        title: str = "Tree",
        persist: bool = True
    ) -> None:
        """Print data as a tree structure."""
        if self.use_rich and self.console:
            tree = Tree(title)
            self._build_tree(tree, data)
            self.print(tree, persist=persist)
        else:
            # Simple tree fallback
            self.print(title, persist=persist)
            self._print_tree_fallback(data, indent=0, persist=persist)
            
    def _build_tree(self, tree: 'Tree', data: Dict[str, Any]) -> None:
        """Recursively build Rich tree."""
        for key, value in data.items():
            if isinstance(value, dict):
                branch = tree.add(key)
                self._build_tree(branch, value)
            else:
                tree.add(f"{key}: {value}")
                
    def _print_tree_fallback(
        self,
        data: Dict[str, Any],
        indent: int = 0,
        persist: bool = True
    ) -> None:
        """Print tree structure without Rich."""
        for key, value in data.items():
            prefix = "  " * indent + "├─ "
            if isinstance(value, dict):
                self.print(f"{prefix}{key}/", persist=persist)
                self._print_tree_fallback(value, indent + 1, persist)
            else:
                self.print(f"{prefix}{key}: {value}", persist=persist)
                
    @contextmanager
    def progress(
        self,
        description: str = "Processing...",
        total: Optional[int] = None
    ):
        """Context manager for progress tracking."""
        if self.use_rich and self.console:
            from rich.progress import SpinnerColumn
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}"),
                BarColumn(bar_width=40, style="cyan", complete_style="green"),
                TextColumn("[green]{task.percentage:>3.0f}%"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(description, total=total)
                yield ProgressTracker(progress, task)
        else:
            # Fallback progress
            yield FallbackProgressTracker(self, description, total)
            
    @contextmanager
    def live_display(self, content: Any = ""):
        """Context manager for live-updating display."""
        if self.use_rich and self.console:
            with Live(content, console=self.console, refresh_per_second=4) as live:
                self._live_context = live
                yield LiveDisplay(live)
                self._live_context = None
        else:
            # Fallback live display
            yield FallbackLiveDisplay(self)
            
    def prompt(
        self,
        question: str,
        default: Optional[str] = None,
        choices: Optional[List[str]] = None
    ) -> str:
        """Get user input with rich prompting."""
        if self.use_rich and self.console:
            return Prompt.ask(question, default=default, choices=choices, console=self.console)
        else:
            # Fallback prompt
            prompt_text = question
            if default:
                prompt_text += f" [{default}]"
            if choices:
                prompt_text += f" ({'/'.join(choices)})"
            prompt_text += ": "
            
            response = input(prompt_text).strip()
            return response if response else (default or "")
            
    def confirm(self, question: str, default: bool = False) -> bool:
        """Get yes/no confirmation from user."""
        if self.use_rich and self.console:
            return Confirm.ask(question, default=default, console=self.console)
        else:
            # Fallback confirm
            suffix = " [Y/n]" if default else " [y/N]"
            response = input(f"{question}{suffix}: ").strip().lower()
            
            if not response:
                return default
            return response.startswith('y')
            
    def clear_last_frame(self) -> None:
        """Clear the last rendered frame."""
        self.buffered_renderer.render_frame([], RenderMode.REPLACE_LAST)
        
    def cleanup(self) -> None:
        """Cleanup terminal state."""
        if self._live_context:
            self._live_context.stop()
        self.buffered_renderer.cleanup()
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class ProgressTracker:
    """Progress tracker for Rich progress bars."""
    
    def __init__(self, progress: 'Progress', task_id: 'TaskID'):
        self.progress = progress
        self.task_id = task_id
        
    def update(self, advance: int = 1) -> None:
        """Advance progress by given amount."""
        self.progress.update(self.task_id, advance=advance)
        
    def set_total(self, total: int) -> None:
        """Set total progress amount."""
        self.progress.update(self.task_id, total=total)
        
    def set_description(self, description: str) -> None:
        """Update progress description."""
        self.progress.update(self.task_id, description=description)


class FallbackProgressTracker:
    """Fallback progress tracker without Rich."""
    
    def __init__(self, terminal: RichTerminal, description: str, total: Optional[int]):
        self.terminal = terminal
        self.description = description
        self.total = total or 100
        self.current = 0
        
    def update(self, advance: int = 1) -> None:
        """Update progress."""
        self.current += advance
        percentage = (self.current / self.total) * 100
        bar_length = 30
        filled_length = int(bar_length * self.current // self.total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        status = f"{self.description} [{bar}] {percentage:.1f}%"
        self.terminal.buffered_renderer.render_status_line(status, replace=True)
        
    def set_total(self, total: int) -> None:
        """Set total."""
        self.total = total
        
    def set_description(self, description: str) -> None:
        """Set description."""
        self.description = description


class LiveDisplay:
    """Live display wrapper for Rich."""
    
    def __init__(self, live: 'Live'):
        self.live = live
        
    def update(self, content: Any) -> None:
        """Update live display content."""
        self.live.update(content)


class FallbackLiveDisplay:
    """Fallback live display without Rich."""
    
    def __init__(self, terminal: RichTerminal):
        self.terminal = terminal
        
    def update(self, content: Any) -> None:
        """Update display content."""
        self.terminal.clear_last_frame()
        self.terminal.print(content, persist=False)


# Convenience functions
def create_rich_terminal(**kwargs) -> RichTerminal:
    """Create a RichTerminal with default settings."""
    return RichTerminal(**kwargs)


def demo_rich_terminal():
    """Demonstrate Rich terminal capabilities."""
    import time
    
    with RichTerminal() as terminal:
        # Show various Rich features
        terminal.print_rule("Rich Terminal Demo", style="bold blue")
        
        terminal.print("This is [bold red]formatted text[/bold red] with Rich markup!", markup=True)
        terminal.print("Emoji support: :rocket: :sparkles: :computer:", emoji=True)
        
        # Panel demo
        terminal.print_panel(
            "This is content inside a beautiful panel!\nMultiple lines are supported.",
            title="Demo Panel",
            subtitle="Pretty borders",
            border_style="green"
        )
        
        # Table demo
        terminal.print_table(
            [
                ["Python", "3.11", "✅"],
                ["Rich", "13.0", "✅"],  
                ["Storm Checker", "0.1.0", "🚀"]
            ],
            headers=["Tool", "Version", "Status"],
            title="Project Dependencies"
        )
        
        # Markdown demo
        terminal.print_markdown("""
# Markdown Support

Rich terminal supports **full markdown** rendering:

- Beautiful bullet points
- **Bold text** and *italic text*
- Code blocks and more!

## This is a subtitle

Pretty neat, right?
        """)
        
        # Code demo
        terminal.print_code('''
def hello_world():
    """A simple Python function."""
    print("Hello, Rich Terminal!")
    return "success"
        ''', language="python", line_numbers=True)
        
        # Progress demo
        terminal.print("\nProgress bar demo:")
        with terminal.progress("Processing items...", total=10) as progress:
            for i in range(10):
                time.sleep(0.2)
                progress.update(1)
                
        terminal.print_rule("Demo Complete! ✨", style="bold green")
        terminal.print("\n[dim]All output above persists in your terminal history![/dim]", markup=True)


if __name__ == "__main__":
    if RICH_AVAILABLE:
        demo_rich_terminal()
    else:
        print("Rich library not available. Install with: pip install rich")