#!/usr/bin/env python3
"""
Storm-Checker Color Scheme
==========================
Custom color palette for beautiful CLI output.
"""

from typing import Optional


class Color:
    """ANSI color code wrapper for terminal colors."""
    
    def __init__(self, hex_color: str, name: str = ""):
        self.hex = hex_color
        self.name = name
        self.rgb = self._hex_to_rgb(hex_color)
        self.ansi = self._rgb_to_ansi(*self.rgb)
    
    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_ansi(self, r: int, g: int, b: int) -> str:
        """Convert RGB to ANSI escape code."""
        return f"\033[38;2;{r};{g};{b}m"
    
    @property
    def bg(self) -> str:
        """Get background color ANSI code."""
        r, g, b = self.rgb
        return f"\033[48;2;{r};{g};{b}m"
    
    def __str__(self) -> str:
        """Return ANSI color code."""
        return self.ansi


# Storm-Checker Color Palette
PALETTE = {
    # Light neutrals
    "light_gray": Color("#dbdbd0", "Light Gray"),
    "cream": Color("#e8e8df", "Cream"),
    "soft_beige": Color("#b3b09f", "Soft Beige"),
    
    # Greens (for success/positive)
    "forest_dark": Color("#364f33", "Forest Dark"),
    "olive_green": Color("#374529", "Olive Green"),
    "sage_green": Color("#466b5d", "Sage Green"),
    "mint_green": Color("#8f897b", "Mint Green"),
    
    # Blues (for info/primary)
    "navy_blue": Color("#003190", "Navy Blue"),
    "sky_blue": Color("#4f8eff", "Sky Blue"),
    "teal_blue": Color("#418791", "Teal Blue"),
    "ocean_blue": Color("#375c69", "Ocean Blue"),
    "steel_blue": Color("#587a84", "Steel Blue"),
    "slate_blue": Color("#344a4d", "Slate Blue"),
    
    # Grays (for secondary/muted)
    "charcoal": Color("#29323b", "Charcoal"),
    "medium_gray": Color("#5e5d5d", "Medium Gray"),
    "gray_purple": Color("#6f6d76", "Gray Purple"),
    "dark_gray": Color("#3e3c42", "Dark Gray"),
    "storm_gray": Color("#304452", "Storm Gray"),
    
    # Warm tones (for warnings/attention)
    "burnt_orange": Color("#f88046", "Burnt Orange"),
    "terracotta": Color("#866068", "Terracotta"),
    "rust": Color("#9e6a55", "Rust"),
    "amber": Color("#be9167", "Amber"),
    "golden": Color("#ccab78", "Golden"),
    "mustard": Color("#996d20", "Mustard"),
    "honey": Color("#a67c23", "Honey"),
    "tan": Color("#b27f52", "Tan"),
    
    # Reds (for errors/critical)
    "crimson": Color("#930235", "Crimson"),
    "brick_red": Color("#8f422c", "Brick Red"),
    "rose": Color("#9c525a", "Rose"),
    
    # Browns (for earth tones)
    "dark_brown": Color("#292225", "Dark Brown"),
    "copper": Color("#995325", "Copper"),
    "mocha": Color("#403125", "Mocha"),
    "sienna": Color("#ab6c2c", "Sienna"),
    "umber": Color("#5e431f", "Umber"),
    
    # Yellows (for highlights)
    "cream_yellow": Color("#fff8c2", "Cream Yellow"),
    "gold_yellow": Color("#ffcc67", "Gold Yellow"),
    
    # Pinks/Purples (for special/accent)
    "magenta": Color("#b1317f", "Magenta"),
    "pink": Color("#d964ab", "Pink"),
    "fuchsia": Color("#c54091", "Fuchsia"),
    "lavender": Color("#f6b0db", "Lavender"),
    
    # Base colors
    "white": Color("#ffffff", "White"),
    "off_white": Color("#eff3ff", "Off White"),
    "black": Color("#000000", "Black"),
}

# Semantic color mappings for Storm-Checker
THEME = {
    # Primary colors for main UI elements
    "primary": PALETTE["teal_blue"],         # #418791
    "primary_light": PALETTE["sky_blue"],    # #4f8eff
    "primary_dark": PALETTE["navy_blue"],    # #003190
    
    # Success/positive feedback
    "success": PALETTE["sage_green"],        # #466b5d
    "success_light": PALETTE["mint_green"],  # #8f897b
    "success_dark": PALETTE["forest_dark"],  # #364f33
    
    # Warnings/attention
    "warning": PALETTE["golden"],            # #ccab78
    "warning_light": PALETTE["cream_yellow"], # #fff8c2
    "warning_dark": PALETTE["mustard"],      # #996d20
    
    # Errors/critical
    "error": PALETTE["rose"],                # #9c525a
    "error_light": PALETTE["pink"],          # #d964ab
    "error_dark": PALETTE["crimson"],        # #930235
    
    # Info/secondary
    "info": PALETTE["steel_blue"],           # #587a84
    "info_light": PALETTE["off_white"],      # #eff3ff
    "info_dark": PALETTE["slate_blue"],      # #344a4d
    
    # Text colors
    "text": PALETTE["charcoal"],             # #29323b
    "text_muted": PALETTE["medium_gray"],    # #5e5d5d
    "text_light": PALETTE["light_gray"],     # #dbdbd0
    
    # Background colors
    "bg": PALETTE["cream"],                  # #e8e8df
    "bg_dark": PALETTE["storm_gray"],        # #304452
    
    # Accent colors for special elements
    "accent": PALETTE["magenta"],            # #b1317f
    "accent_light": PALETTE["lavender"],     # #f6b0db
    "accent_dark": PALETTE["fuchsia"],       # #c54091
    
    # Educational specific
    "learn": PALETTE["ocean_blue"],          # #375c69
    "practice": PALETTE["amber"],            # #be9167
    "master": PALETTE["honey"],              # #a67c23
}

# ANSI control codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"
HIDDEN = "\033[8m"
STRIKETHROUGH = "\033[9m"

# Cursor control
CURSOR_UP = "\033[A"
CURSOR_DOWN = "\033[B"
CURSOR_FORWARD = "\033[C"
CURSOR_BACK = "\033[D"
CURSOR_SAVE = "\033[s"
CURSOR_RESTORE = "\033[u"
CURSOR_HIDE = "\033[?25l"
CURSOR_SHOW = "\033[?25h"

# Screen control
CLEAR_SCREEN = "\033[2J\033[H"
CLEAR_LINE = "\033[K"
CLEAR_TO_END = "\033[0J"
CLEAR_TO_START = "\033[1J"


class ColorPrinter:
    """Helper class for printing with colors."""
    
    @staticmethod
    def primary(text: str, bold: bool = False) -> str:
        """Print text in primary color."""
        style = BOLD if bold else ""
        return f"{style}{THEME['primary']}{text}{RESET}"
    
    @staticmethod
    def success(text: str, bold: bool = False) -> str:
        """Print text in success color."""
        style = BOLD if bold else ""
        return f"{style}{THEME['success']}{text}{RESET}"
    
    @staticmethod
    def warning(text: str, bold: bool = False) -> str:
        """Print text in warning color."""
        style = BOLD if bold else ""
        return f"{style}{THEME['warning']}{text}{RESET}"
    
    @staticmethod
    def error(text: str, bold: bool = False) -> str:
        """Print text in error color."""
        style = BOLD if bold else ""
        return f"{style}{THEME['error']}{text}{RESET}"
    
    @staticmethod
    def info(text: str, bold: bool = False) -> str:
        """Print text in info color."""
        style = BOLD if bold else ""
        return f"{style}{THEME['info']}{text}{RESET}"
    
    @staticmethod
    def learn(text: str, bold: bool = False) -> str:
        """Print text in learning color."""
        style = BOLD if bold else ""
        return f"{style}{THEME['learn']}{text}{RESET}"
    
    @staticmethod
    def custom(text: str, color_name: str, bold: bool = False) -> str:
        """Print text in custom color from palette."""
        if color_name not in PALETTE:
            return text
        style = BOLD if bold else ""
        return f"{style}{PALETTE[color_name]}{text}{RESET}"
    
    @staticmethod
    def gradient(text: str, start_color: str, end_color: str) -> str:
        """Print text with a gradient effect (simplified)."""
        # For terminal, we'll just use the start color
        # True gradients would require more complex handling
        if start_color in PALETTE:
            return f"{PALETTE[start_color]}{text}{RESET}"
        return text


# Convenience functions
def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a formatted header."""
    print(f"\n{THEME['primary']}{BOLD}{'=' * 60}{RESET}")
    print(f"{THEME['primary']}{BOLD}{title.center(60)}{RESET}")
    if subtitle:
        print(f"{THEME['info']}{subtitle.center(60)}{RESET}")
    print(f"{THEME['primary']}{BOLD}{'=' * 60}{RESET}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{THEME['success']}✅ {message}{RESET}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{THEME['error']}❌ {message}{RESET}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{THEME['warning']}⚠️  {message}{RESET}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{THEME['info']}ℹ️  {message}{RESET}")


def print_learn(message: str) -> None:
    """Print a learning message."""
    print(f"{THEME['learn']}📚 {message}{RESET}")


# Rich integration
try:
    from rich.theme import Theme as RichTheme
    from rich.color import Color as RichColor
    from rich.style import Style as RichStyle
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    RichTheme = None
    RichColor = None
    RichStyle = None


def get_rich_theme() -> Optional['RichTheme']:
    """Get Rich theme based on our color palette."""
    if not RICH_AVAILABLE:
        return None
        
    # Convert our theme to Rich theme
    rich_styles = {}
    
    # Map our semantic colors to Rich styles
    rich_styles.update({
        "primary": f"bold {THEME['primary'].hex}",
        "success": f"bold {THEME['success'].hex}",
        "warning": f"bold {THEME['warning'].hex}",
        "error": f"bold {THEME['error'].hex}",
        "info": THEME['info'].hex,
        "learn": f"bold {THEME['learn'].hex}",
        "accent": THEME['accent'].hex,
        
        # Text styles
        "text": THEME['text'].hex,
        "text.muted": THEME['text_muted'].hex,
        "text.light": THEME['text_light'].hex,
        
        # UI elements
        "border": THEME['primary'].hex,
        "border.success": THEME['success'].hex,
        "border.warning": THEME['warning'].hex,
        "border.error": THEME['error'].hex,
        
        # Progress and status
        "progress.bar": THEME['primary'].hex,
        "progress.complete": THEME['success'].hex,
        "progress.remaining": THEME['text_muted'].hex,
        
        # Educational elements
        "tutorial.title": f"bold {THEME['learn'].hex}",
        "tutorial.subtitle": THEME['info'].hex,
        "question.correct": f"bold {THEME['success'].hex}",
        "question.incorrect": f"bold {THEME['error'].hex}",
        "achievement": f"bold {THEME['accent'].hex}",
    })
    
    return RichTheme(rich_styles)


def get_rich_color(color_name: str) -> Optional['RichColor']:
    """Get a Rich Color object from our palette."""
    if not RICH_AVAILABLE:
        return None
        
    if color_name in THEME:
        return RichColor.parse(THEME[color_name].hex)
    elif color_name in PALETTE:
        return RichColor.parse(PALETTE[color_name].hex)
    else:
        return None


def create_rich_style(
    color_name: str,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False
) -> Optional['RichStyle']:
    """Create a Rich Style from our color palette."""
    if not RICH_AVAILABLE:
        return None
        
    rich_color = get_rich_color(color_name)
    if not rich_color:
        return None
        
    return RichStyle(
        color=rich_color,
        bold=bold,
        italic=italic,
        underline=underline
    )


class EnhancedColorPrinter(ColorPrinter):
    """Enhanced color printer with Rich integration."""
    
    @staticmethod
    def rich_text(text: str, style_name: str, **kwargs) -> str:
        """Create Rich markup text."""
        if not RICH_AVAILABLE:
            # Fallback to regular color printing
            if style_name in ['primary', 'success', 'warning', 'error', 'info', 'learn']:
                return getattr(ColorPrinter, style_name)(text, **kwargs)
            return text
            
        # Create Rich markup
        markup_parts = []
        
        if kwargs.get('bold', False):
            markup_parts.append('bold')
        if kwargs.get('italic', False):
            markup_parts.append('italic')
        if kwargs.get('underline', False):
            markup_parts.append('underline')
            
        # Add color
        color = get_rich_color(style_name)
        if color:
            markup_parts.append(color.name)
            
        if markup_parts:
            style_str = ' '.join(markup_parts)
            return f"[{style_str}]{text}[/{style_str}]"
        else:
            return text
            
    @staticmethod
    def tutorial_title(text: str) -> str:
        """Format tutorial title."""
        return EnhancedColorPrinter.rich_text(text, 'learn', bold=True)
        
    @staticmethod
    def question_text(text: str, correct: Optional[bool] = None) -> str:
        """Format question text with optional correctness indicator."""
        if correct is True:
            return EnhancedColorPrinter.rich_text(f"✅ {text}", 'success', bold=True)
        elif correct is False:
            return EnhancedColorPrinter.rich_text(f"❌ {text}", 'error', bold=True)
        else:
            return EnhancedColorPrinter.rich_text(f"❓ {text}", 'warning', bold=True)
            
    @staticmethod
    def achievement(text: str) -> str:
        """Format achievement text."""
        return EnhancedColorPrinter.rich_text(f"🏆 {text}", 'accent', bold=True)
        
    @staticmethod
    def code_highlight(text: str) -> str:
        """Format code text."""
        return EnhancedColorPrinter.rich_text(text, 'info')
        
    @staticmethod
    def progress_text(current: int, total: int, label: str = "Progress") -> str:
        """Format progress text."""
        percentage = (current / total) * 100 if total > 0 else 0
        return EnhancedColorPrinter.rich_text(
            f"{label}: {current}/{total} ({percentage:.0f}%)",
            'primary'
        )


# Enhanced convenience functions with Rich support
def print_rich_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a Rich-formatted header."""
    if RICH_AVAILABLE:
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.text import Text
            from rich.align import Align
            
            console = Console()
            
            title_text = Text(title, style="bold primary")
            content = Align.center(title_text)
            
            if subtitle:
                subtitle_text = Text(subtitle, style="info")
                content = Align.center(Text.assemble(title_text, "\n", subtitle_text))
                
            panel = Panel(content, style="primary")
            console.print(panel)
            return
        except:
            pass
            
    # Fallback to regular header
    print_header(title, subtitle)


def print_rich_success(message: str) -> None:
    """Print Rich-formatted success message."""
    if RICH_AVAILABLE:
        try:
            from rich.console import Console
            Console().print(f"✅ {message}", style="bold success")
            return
        except:
            pass
    print_success(message)


def print_rich_error(message: str) -> None:
    """Print Rich-formatted error message."""
    if RICH_AVAILABLE:
        try:
            from rich.console import Console
            Console().print(f"❌ {message}", style="bold error")
            return
        except:
            pass
    print_error(message)


def print_rich_warning(message: str) -> None:
    """Print Rich-formatted warning message."""
    if RICH_AVAILABLE:
        try:
            from rich.console import Console
            Console().print(f"⚠️  {message}", style="bold warning")
            return
        except:
            pass
    print_warning(message)


def print_rich_info(message: str) -> None:
    """Print Rich-formatted info message."""
    if RICH_AVAILABLE:
        try:
            from rich.console import Console
            Console().print(f"ℹ️  {message}", style="info")
            return
        except:
            pass
    print_info(message)


def print_rich_learn(message: str) -> None:
    """Print Rich-formatted learning message."""
    if RICH_AVAILABLE:
        try:
            from rich.console import Console
            Console().print(f"📚 {message}", style="bold learn")
            return
        except:
            pass
    print_learn(message)


# Demo function to show all colors
def demo_colors() -> None:
    """Display all available colors for reference."""
    print_header("Storm-Checker Color Palette", "Beautiful CLI colors")
    
    print(f"{BOLD}Theme Colors:{RESET}")
    for name, color in THEME.items():
        print(f"  {color}■■■ {name:<20}{RESET} {color}Sample text in this color{RESET}")
    
    print(f"\n{BOLD}Full Palette:{RESET}")
    for name, color in sorted(PALETTE.items()):
        print(f"  {color}■■■ {name:<20}{RESET} {color.hex} - {color}Sample text{RESET}")
    
    print(f"\n{BOLD}Text Styles:{RESET}")
    print(f"  {BOLD}Bold text{RESET}")
    print(f"  {DIM}Dim text{RESET}")
    print(f"  {ITALIC}Italic text{RESET}")
    print(f"  {UNDERLINE}Underlined text{RESET}")
    print(f"  {STRIKETHROUGH}Strikethrough text{RESET}")
    
    print(f"\n{BOLD}Usage Examples:{RESET}")
    print_success("This is a success message")
    print_error("This is an error message")
    print_warning("This is a warning message")
    print_info("This is an info message")
    print_learn("This is a learning tip")
    
    # Rich integration demo
    if RICH_AVAILABLE:
        print(f"\n{BOLD}Rich Integration Examples:{RESET}")
        print_rich_success("Rich success message with better formatting")
        print_rich_error("Rich error message with enhanced styling")
        print_rich_warning("Rich warning with improved visual hierarchy")
        print_rich_info("Rich info message with better typography")
        print_rich_learn("Rich learning tip with enhanced colors")


def demo_rich_integration():
    """Demonstrate Rich integration capabilities."""
    if not RICH_AVAILABLE:
        print("Rich library not available. Install with: pip install rich")
        return
        
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        
        console = Console(theme=get_rich_theme())
        
        print_rich_header("Rich Integration Demo", "Enhanced Colors with Rich")
        
        # Color palette table
        table = Table(title="Color Palette")
        table.add_column("Name", style="bold")
        table.add_column("Hex", style="dim")
        table.add_column("Sample", style="bold")
        
        for name, color in list(THEME.items())[:10]:  # Show first 10
            table.add_row(name, color.hex, f"Sample text", style=f"color({color.hex})")
            
        console.print(table)
        
        # Style examples
        console.print(Panel(
            Text.assemble(
                ("Primary: ", "bold primary"), ("Important information\n", "primary"),
                ("Success: ", "bold success"), ("Operation completed\n", "success"),
                ("Warning: ", "bold warning"), ("Attention needed\n", "warning"),
                ("Error: ", "bold error"), ("Something went wrong\n", "error"),
                ("Learn: ", "bold learn"), ("Educational content", "learn"),
            ),
            title="Themed Styles",
            style="primary"
        ))
        
    except Exception as e:
        print(f"Rich demo failed: {e}")
        demo_colors()  # Fallback to regular demo


if __name__ == "__main__":
    demo_colors()