#!/usr/bin/env python3
"""
Modern Keyboard Handler
=======================
World-class keyboard input handling for CLI applications.
"""

import sys
import termios
import tty
import select
from typing import Optional, Callable, Dict, Any, List
from enum import Enum
from dataclasses import dataclass


class KeyCode(Enum):
    """Standard key codes for cross-platform compatibility."""
    # Navigation
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    HOME = "home"
    END = "end"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"
    
    # Control
    ENTER = "enter"
    ESCAPE = "escape"
    TAB = "tab"
    BACKSPACE = "backspace"
    DELETE = "delete"
    
    # Function keys
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"
    
    # Modifiers (when combined with other keys)
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    
    # Special
    SPACE = "space"
    UNKNOWN = "unknown"


@dataclass
class KeyPress:
    """Represents a key press event."""
    key: KeyCode
    char: Optional[str] = None
    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    raw_sequence: str = ""


class KeyboardHandler:
    """
    Modern keyboard input handler with support for:
    - Arrow keys and navigation
    - Function keys
    - Modifier keys (Ctrl, Alt, Shift)
    - Cross-platform compatibility
    - Non-blocking input
    """
    
    def __init__(self):
        """Initialize keyboard handler."""
        self.key_bindings: Dict[str, Callable] = {}
        self.key_sequences = self._build_key_sequences()
        self._original_settings: Optional[List] = None
        self._raw_mode_active = False
        
    def _build_key_sequences(self) -> Dict[str, KeyCode]:
        """Build mapping of escape sequences to key codes."""
        return {
            # Arrow keys
            '\x1b[A': KeyCode.UP,
            '\x1b[B': KeyCode.DOWN,
            '\x1b[C': KeyCode.RIGHT,
            '\x1b[D': KeyCode.LEFT,
            
            # Home/End
            '\x1b[H': KeyCode.HOME,
            '\x1b[F': KeyCode.END,
            '\x1b[1~': KeyCode.HOME,
            '\x1b[4~': KeyCode.END,
            
            # Page Up/Down
            '\x1b[5~': KeyCode.PAGE_UP,
            '\x1b[6~': KeyCode.PAGE_DOWN,
            
            # Delete
            '\x1b[3~': KeyCode.DELETE,
            
            # Function keys
            '\x1bOP': KeyCode.F1,
            '\x1bOQ': KeyCode.F2,
            '\x1bOR': KeyCode.F3,
            '\x1bOS': KeyCode.F4,
            '\x1b[15~': KeyCode.F5,
            '\x1b[17~': KeyCode.F6,
            '\x1b[18~': KeyCode.F7,
            '\x1b[19~': KeyCode.F8,
            '\x1b[20~': KeyCode.F9,
            '\x1b[21~': KeyCode.F10,
            '\x1b[23~': KeyCode.F11,
            '\x1b[24~': KeyCode.F12,
            
            # Special sequences
            '\x1b[Z': KeyCode.TAB,  # Shift+Tab
        }
        
    def enter_raw_mode(self) -> None:
        """Enter raw terminal mode for character-by-character input."""
        if sys.stdin.isatty() and not self._raw_mode_active:
            self._original_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
            self._raw_mode_active = True
            
    def exit_raw_mode(self) -> None:
        """Exit raw terminal mode."""
        if self._original_settings and self._raw_mode_active:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._original_settings)
            self._raw_mode_active = False
            self._original_settings = None
            
    def read_key(self, timeout: Optional[float] = None) -> Optional[KeyPress]:
        """
        Read a single key press.
        
        Args:
            timeout: Maximum time to wait for input (None = blocking)
            
        Returns:
            KeyPress object or None if timeout
        """
        if not sys.stdin.isatty():
            # Fallback for non-interactive terminals
            try:
                char = sys.stdin.read(1)
                return self._parse_key(char)
            except:
                return None
                
        # Check if input is available
        if timeout is not None:
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if not ready:
                return None
                
        try:
            # Read first character
            char = sys.stdin.read(1)
            
            # Handle escape sequences
            if char == '\x1b':
                sequence = char
                
                # Read additional characters for escape sequences
                for _ in range(10):  # Max sequence length
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        next_char = sys.stdin.read(1)
                        sequence += next_char
                        
                        # Check if we have a complete sequence
                        if sequence in self.key_sequences:
                            return KeyPress(
                                key=self.key_sequences[sequence],
                                raw_sequence=sequence
                            )
                    else:
                        break
                        
                # If no sequence matched, it's just escape
                if sequence == '\x1b':
                    return KeyPress(key=KeyCode.ESCAPE, raw_sequence=sequence)
                else:
                    return KeyPress(key=KeyCode.UNKNOWN, raw_sequence=sequence)
                    
            return self._parse_key(char)
            
        except (KeyboardInterrupt, EOFError):
            return KeyPress(key=KeyCode.ESCAPE, ctrl=True)
            
    def _parse_key(self, char: str) -> KeyPress:
        """Parse a single character into a KeyPress."""
        # Control characters
        if ord(char) < 32:
            return self._parse_control_char(char)
            
        # Regular characters
        if char == ' ':
            return KeyPress(key=KeyCode.SPACE, char=char)
        elif char.isprintable():
            return KeyPress(
                key=KeyCode.UNKNOWN,
                char=char,
                shift=char.isupper()
            )
        else:
            return KeyPress(key=KeyCode.UNKNOWN, raw_sequence=char)
            
    def _parse_control_char(self, char: str) -> KeyPress:
        """Parse control characters."""
        ord_char = ord(char)
        
        if ord_char == 10 or ord_char == 13:  # \n or \r
            return KeyPress(key=KeyCode.ENTER)
        elif ord_char == 9:  # \t
            return KeyPress(key=KeyCode.TAB)
        elif ord_char == 127 or ord_char == 8:  # DEL or BS
            return KeyPress(key=KeyCode.BACKSPACE)
        elif ord_char == 27:  # ESC
            return KeyPress(key=KeyCode.ESCAPE)
        elif 1 <= ord_char <= 26:  # Ctrl+A through Ctrl+Z
            ctrl_char = chr(ord('a') + ord_char - 1)
            return KeyPress(
                key=KeyCode.UNKNOWN,
                char=ctrl_char,
                ctrl=True
            )
        else:
            return KeyPress(key=KeyCode.UNKNOWN, raw_sequence=char)
            
    def bind_key(self, key_pattern: str, callback: Callable[[KeyPress], Any]) -> None:
        """
        Bind a key pattern to a callback function.
        
        Args:
            key_pattern: Key pattern (e.g., "q", "ctrl+c", "up", "f1")
            callback: Function to call when key is pressed
        """
        self.key_bindings[key_pattern.lower()] = callback
        
    def handle_key(self, key_press: KeyPress) -> bool:
        """
        Handle a key press using registered bindings.
        
        Args:
            key_press: The key press to handle
            
        Returns:
            True if key was handled, False otherwise
        """
        # Try exact key match first
        key_pattern = self._key_press_to_pattern(key_press)
        
        if key_pattern in self.key_bindings:
            self.key_bindings[key_pattern](key_press)
            return True
            
        # Try character match for printable characters
        if key_press.char and key_press.char.lower() in self.key_bindings:
            self.key_bindings[key_press.char.lower()](key_press)
            return True
            
        return False
        
    def _key_press_to_pattern(self, key_press: KeyPress) -> str:
        """Convert a KeyPress to a pattern string."""
        parts = []
        
        if key_press.ctrl:
            parts.append("ctrl")
        if key_press.alt:
            parts.append("alt")
        if key_press.shift and key_press.key != KeyCode.UNKNOWN:
            parts.append("shift")
            
        if key_press.key != KeyCode.UNKNOWN:
            parts.append(key_press.key.value)
        elif key_press.char:
            parts.append(key_press.char.lower())
            
        return "+".join(parts)
        
    def create_input_loop(
        self,
        prompt: str = "",
        quit_keys: Optional[List[str]] = None
    ) -> Callable:
        """
        Create an input loop context manager.
        
        Args:
            prompt: Prompt to display
            quit_keys: Keys that will exit the loop
            
        Returns:
            Context manager for input loop
        """
        if quit_keys is None:
            quit_keys = ["q", "ctrl+c", "escape"]
            
        class InputLoop:
            def __init__(self, handler: KeyboardHandler):
                self.handler = handler
                self.running = False
                
            def __enter__(self):
                self.handler.enter_raw_mode()
                self.running = True
                if prompt:
                    print(prompt, end='', flush=True)
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.handler.exit_raw_mode()
                self.running = False
                
            def run(self) -> Optional[KeyPress]:
                """Run one iteration of the input loop."""
                if not self.running:
                    return None
                    
                key_press = self.handler.read_key(timeout=0.1)
                if key_press:
                    # Check for quit keys
                    pattern = self.handler._key_press_to_pattern(key_press)
                    if pattern in quit_keys or (key_press.char and key_press.char.lower() in quit_keys):
                        self.running = False
                        return None
                        
                    # Handle key bindings
                    self.handler.handle_key(key_press)
                    
                return key_press
                
        return InputLoop(self)
        
    def wait_for_key(self, valid_keys: Optional[List[str]] = None) -> KeyPress:
        """
        Wait for a specific key press.
        
        Args:
            valid_keys: List of valid key patterns (None = any key)
            
        Returns:
            The key press that was pressed
        """
        self.enter_raw_mode()
        try:
            while True:
                key_press = self.read_key()
                if key_press:
                    if valid_keys is None:
                        return key_press
                        
                    pattern = self._key_press_to_pattern(key_press)
                    if (pattern in valid_keys or 
                        (key_press.char and key_press.char.lower() in valid_keys)):
                        return key_press
        finally:
            self.exit_raw_mode()
            
    def __enter__(self):
        """Context manager entry."""
        self.enter_raw_mode()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.exit_raw_mode()


# Convenience functions
def wait_for_any_key(prompt: str = "Press any key to continue...") -> KeyPress:
    """Wait for any key press."""
    handler = KeyboardHandler()
    print(prompt, end='', flush=True)
    key_press = handler.wait_for_key()
    print()  # New line after key press
    return key_press


def wait_for_specific_key(
    keys: List[str],
    prompt: str = "Press a key: "
) -> KeyPress:
    """Wait for a specific key from a list."""
    handler = KeyboardHandler()
    print(f"{prompt}({'/'.join(keys)})", end='', flush=True)
    key_press = handler.wait_for_key(keys)
    print()  # New line after key press
    return key_press


def create_navigation_handler() -> KeyboardHandler:
    """Create a keyboard handler with common navigation bindings."""
    handler = KeyboardHandler()
    
    # Add common navigation bindings
    handler.bind_key("q", lambda k: print("\nQuitting..."))
    handler.bind_key("h", lambda k: print("\nHelp: Use arrow keys to navigate, 'q' to quit"))
    handler.bind_key("ctrl+c", lambda k: print("\nInterrupted!"))
    
    return handler


# Demo function
def demo_keyboard_handler():
    """Demonstrate keyboard handler capabilities."""
    print("=== Keyboard Handler Demo ===")
    print("Try different keys. Press 'q' to quit.")
    print("Special keys: arrows, function keys, ctrl combinations, etc.")
    print()
    
    handler = KeyboardHandler()
    
    # Set up key bindings
    handler.bind_key("h", lambda k: print("Help: Arrow keys navigate, F1-F12 for functions, 'q' to quit"))
    handler.bind_key("ctrl+c", lambda k: print("Ctrl+C detected!"))
    handler.bind_key("up", lambda k: print("↑ Up arrow"))
    handler.bind_key("down", lambda k: print("↓ Down arrow"))
    handler.bind_key("left", lambda k: print("← Left arrow"))
    handler.bind_key("right", lambda k: print("→ Right arrow"))
    handler.bind_key("f1", lambda k: print("🔑 F1 pressed"))
    handler.bind_key("space", lambda k: print("⎵ Space pressed"))
    
    with handler.create_input_loop("Ready (press 'h' for help): ") as loop:
        while loop.running:
            key_press = loop.run()
            if key_press and not handler.handle_key(key_press):
                # Show unhandled keys
                if key_press.char:
                    print(f"Character: '{key_press.char}'", end=' ')
                print(f"Key: {key_press.key.value}")
                if key_press.ctrl:
                    print("  [with Ctrl]")
                if key_press.alt:
                    print("  [with Alt]")
                if key_press.shift:
                    print("  [with Shift]")
                print()
                
    print("\nDemo complete!")


if __name__ == "__main__":
    demo_keyboard_handler()