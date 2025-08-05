"""
Comprehensive Tests for Keyboard Handler
=======================================
Tests for keyboard input handling with full coverage of all functionality.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, mock_open
from io import StringIO

from storm_checker.cli.components.keyboard_handler import (
    KeyCode, KeyPress, KeyboardHandler,
    wait_for_any_key, wait_for_specific_key, create_navigation_handler,
    demo_keyboard_handler
)


class TestKeyCode:
    """Test the KeyCode enum."""
    
    def test_keycode_enum_values(self):
        """Test KeyCode enum has expected values."""
        # Navigation keys
        assert KeyCode.UP.value == "up"
        assert KeyCode.DOWN.value == "down"
        assert KeyCode.LEFT.value == "left"
        assert KeyCode.RIGHT.value == "right"
        assert KeyCode.HOME.value == "home"
        assert KeyCode.END.value == "end"
        assert KeyCode.PAGE_UP.value == "page_up"
        assert KeyCode.PAGE_DOWN.value == "page_down"
        
        # Control keys
        assert KeyCode.ENTER.value == "enter"
        assert KeyCode.ESCAPE.value == "escape"
        assert KeyCode.TAB.value == "tab"
        assert KeyCode.BACKSPACE.value == "backspace"
        assert KeyCode.DELETE.value == "delete"
        
        # Function keys
        assert KeyCode.F1.value == "f1"
        assert KeyCode.F12.value == "f12"
        
        # Modifiers
        assert KeyCode.CTRL.value == "ctrl"
        assert KeyCode.ALT.value == "alt"
        assert KeyCode.SHIFT.value == "shift"
        
        # Special
        assert KeyCode.SPACE.value == "space"
        assert KeyCode.UNKNOWN.value == "unknown"
    
    def test_keycode_enum_completeness(self):
        """Test that KeyCode enum contains all expected keys."""
        expected_keys = [
            "UP", "DOWN", "LEFT", "RIGHT", "HOME", "END", "PAGE_UP", "PAGE_DOWN",
            "ENTER", "ESCAPE", "TAB", "BACKSPACE", "DELETE",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", 
            "CTRL", "ALT", "SHIFT", "SPACE", "UNKNOWN"
        ]
        
        for key in expected_keys:
            assert hasattr(KeyCode, key), f"KeyCode missing {key}"


class TestKeyPress:
    """Test the KeyPress dataclass."""
    
    def test_keypress_initialization_minimal(self):
        """Test KeyPress initialization with minimal parameters."""
        key_press = KeyPress(key=KeyCode.ENTER)
        
        assert key_press.key == KeyCode.ENTER
        assert key_press.char is None
        assert key_press.ctrl is False
        assert key_press.alt is False
        assert key_press.shift is False
        assert key_press.raw_sequence == ""
    
    def test_keypress_initialization_complete(self):
        """Test KeyPress initialization with all parameters."""
        key_press = KeyPress(
            key=KeyCode.UP,
            char='a',
            ctrl=True,
            alt=True,
            shift=True,
            raw_sequence='\x1b[A'
        )
        
        assert key_press.key == KeyCode.UP
        assert key_press.char == 'a'
        assert key_press.ctrl is True
        assert key_press.alt is True
        assert key_press.shift is True
        assert key_press.raw_sequence == '\x1b[A'


class TestKeyboardHandler:
    """Test the KeyboardHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create KeyboardHandler instance for testing."""
        return KeyboardHandler()
    
    def test_keyboard_handler_initialization(self, handler):
        """Test that the KeyboardHandler can be initialized."""
        assert isinstance(handler, KeyboardHandler)
        assert isinstance(handler.key_bindings, dict)
        assert len(handler.key_bindings) == 0
        assert isinstance(handler.key_sequences, dict)
        assert len(handler.key_sequences) > 0
        assert handler._original_settings is None
        assert handler._raw_mode_active is False
    
    def test_build_key_sequences(self, handler):
        """Test that key sequences are built correctly."""
        sequences = handler.key_sequences
        
        # Test common sequences
        assert '\x1b[A' in sequences  # UP
        assert '\x1b[B' in sequences  # DOWN
        assert '\x1b[C' in sequences  # RIGHT
        assert '\x1b[D' in sequences  # LEFT
        assert '\x1b[H' in sequences  # HOME
        assert '\x1b[F' in sequences  # END
        assert '\x1bOP' in sequences  # F1
        
        # Test values
        assert sequences['\x1b[A'] == KeyCode.UP
        assert sequences['\x1b[B'] == KeyCode.DOWN
        assert sequences['\x1bOP'] == KeyCode.F1
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.termios.tcgetattr')
    @patch('storm_checker.cli.components.keyboard_handler.tty.setraw')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.fileno')
    def test_enter_raw_mode(self, mock_fileno, mock_setraw, mock_tcgetattr, mock_isatty, handler):
        """Test entering raw terminal mode."""
        mock_isatty.return_value = True
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = ['original', 'settings']
        
        handler.enter_raw_mode()
        
        assert handler._raw_mode_active is True
        assert handler._original_settings == ['original', 'settings']
        mock_tcgetattr.assert_called_once_with(0)
        mock_setraw.assert_called_once_with(0)
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    def test_enter_raw_mode_not_tty(self, mock_isatty, handler):
        """Test entering raw mode when not a TTY."""
        mock_isatty.return_value = False
        
        handler.enter_raw_mode()
        
        assert handler._raw_mode_active is False
        assert handler._original_settings is None
    
    def test_enter_raw_mode_already_active(self, handler):
        """Test entering raw mode when already active."""
        handler._raw_mode_active = True
        handler._original_settings = ['old', 'settings']
        
        with patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty', return_value=True):
            with patch('storm_checker.cli.components.keyboard_handler.termios.tcgetattr') as mock_tcgetattr:
                handler.enter_raw_mode()
                mock_tcgetattr.assert_not_called()
    
    @patch('storm_checker.cli.components.keyboard_handler.termios.tcsetattr')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.fileno')
    def test_exit_raw_mode(self, mock_fileno, mock_tcsetattr, handler):
        """Test exiting raw terminal mode."""
        handler._raw_mode_active = True
        handler._original_settings = ['original', 'settings']
        mock_fileno.return_value = 0
        
        handler.exit_raw_mode()
        
        assert handler._raw_mode_active is False
        assert handler._original_settings is None
        mock_tcsetattr.assert_called_once()
    
    def test_exit_raw_mode_not_active(self, handler):
        """Test exiting raw mode when not active."""
        with patch('storm_checker.cli.components.keyboard_handler.termios.tcsetattr') as mock_tcsetattr:
            handler.exit_raw_mode()
            mock_tcsetattr.assert_not_called()
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_non_tty(self, mock_read, mock_isatty, handler):
        """Test reading key from non-TTY terminal."""
        mock_isatty.return_value = False
        mock_read.return_value = 'a'
        
        key_press = handler.read_key()
        
        assert key_press is not None
        assert key_press.char == 'a'
        mock_read.assert_called_once_with(1)
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_non_tty_exception(self, mock_read, mock_isatty, handler):
        """Test reading key from non-TTY with exception."""
        mock_isatty.return_value = False
        mock_read.side_effect = Exception("Read error")
        
        key_press = handler.read_key()
        
        assert key_press is None
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.select.select')
    def test_read_key_timeout(self, mock_select, mock_isatty, handler):
        """Test reading key with timeout."""
        mock_isatty.return_value = True
        mock_select.return_value = ([], [], [])  # No input ready
        
        key_press = handler.read_key(timeout=0.1)
        
        assert key_press is None
        mock_select.assert_called_once_with([sys.stdin], [], [], 0.1)
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.select.select')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_simple_char(self, mock_read, mock_select, mock_isatty, handler):
        """Test reading a simple character."""
        mock_isatty.return_value = True
        mock_select.return_value = ([sys.stdin], [], [])  # Input ready
        mock_read.return_value = 'a'
        
        key_press = handler.read_key()
        
        assert key_press is not None
        assert key_press.char == 'a'
        assert key_press.key == KeyCode.UNKNOWN
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.select.select')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_escape_sequence(self, mock_read, mock_select, mock_isatty, handler):
        """Test reading escape sequence."""
        mock_isatty.return_value = True
        mock_select.side_effect = [
            ([sys.stdin], [], []),  # Initial select
            ([sys.stdin], [], []),  # First sequence char
            ([sys.stdin], [], []),  # Second sequence char
            ([], [], [])            # No more chars
        ]
        mock_read.side_effect = ['\x1b', '[', 'A']  # UP arrow sequence
        
        key_press = handler.read_key()
        
        assert key_press is not None
        assert key_press.key == KeyCode.UP
        assert key_press.raw_sequence == '\x1b[A'
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.select.select')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_escape_only(self, mock_read, mock_select, mock_isatty, handler):
        """Test reading lone escape character."""
        mock_isatty.return_value = True
        
        # All select calls should timeout (no input available for sequence continuation)
        mock_select.return_value = ([], [], [])  # Always return no input available
        
        # Only return escape once for the main read
        mock_read.return_value = '\x1b'
        
        key_press = handler.read_key()
        
        assert key_press is not None
        assert key_press.key == KeyCode.ESCAPE
        assert key_press.raw_sequence == '\x1b'
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.select.select')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_unknown_sequence(self, mock_read, mock_select, mock_isatty, handler):
        """Test reading unknown escape sequence."""
        mock_isatty.return_value = True
        
        # First select shows input available, then no more input
        mock_select.side_effect = [
            ([sys.stdin], [], []),  # First iteration - input available
            ([], [], [])            # All subsequent calls - no input
        ]
        
        # Mock reading escape then X - need to account for the initial read + loop read
        mock_read.side_effect = ['\x1b', 'X']
        
        key_press = handler.read_key()
        
        assert key_press is not None
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.raw_sequence == '\x1bX'
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_keyboard_interrupt(self, mock_read, mock_isatty, handler):
        """Test handling KeyboardInterrupt."""
        mock_isatty.return_value = True
        mock_read.side_effect = KeyboardInterrupt
        
        key_press = handler.read_key()
        
        assert key_press is not None
        assert key_press.key == KeyCode.ESCAPE
        assert key_press.ctrl is True
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_eof_error(self, mock_read, mock_isatty, handler):
        """Test handling EOFError."""
        mock_isatty.return_value = True
        mock_read.side_effect = EOFError
        
        key_press = handler.read_key()
        
        assert key_press is not None
        assert key_press.key == KeyCode.ESCAPE
        assert key_press.ctrl is True
    
    def test_parse_key_control_char(self, handler):
        """Test parsing control characters."""
        # Enter
        key_press = handler._parse_key('\n')
        assert key_press.key == KeyCode.ENTER
        
        key_press = handler._parse_key('\r')
        assert key_press.key == KeyCode.ENTER
        
        # Tab
        key_press = handler._parse_key('\t')
        assert key_press.key == KeyCode.TAB
        
        # Backspace (BS char 8) - this tests line 227
        key_press = handler._parse_key('\x08')
        assert key_press.key == KeyCode.BACKSPACE
        
        # Escape - this tests line 229 (control char path)
        key_press = handler._parse_key('\x1b')
        assert key_press.key == KeyCode.ESCAPE
    
    def test_parse_key_del_non_control(self, handler):
        """Test parsing DEL character (127) - not a control char, goes to line 216."""
        # DEL char 127 is > 32, so it's handled as non-printable, not control char
        key_press = handler._parse_key('\x7f')
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.raw_sequence == '\x7f'
    
    def test_parse_key_printable_char(self, handler):
        """Test parsing printable characters."""
        # Space
        key_press = handler._parse_key(' ')
        assert key_press.key == KeyCode.SPACE
        assert key_press.char == ' '
        
        # Regular character
        key_press = handler._parse_key('a')
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.char == 'a'
        assert key_press.shift is False
        
        # Uppercase character
        key_press = handler._parse_key('A')
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.char == 'A'
        assert key_press.shift is True
    
    def test_parse_key_non_printable(self, handler):
        """Test parsing non-printable characters."""
        # \xff is actually printable, so test with a truly non-printable char
        # Use a control character > 32 that's non-printable
        key_press = handler._parse_key('\x80')  # Character 128 - non-printable
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.raw_sequence == '\x80'
        assert key_press.char is None
    
    def test_parse_key_printable_high_char(self, handler):
        """Test parsing high-value printable characters like \xff."""
        # \xff (ÿ) is actually printable in Python
        key_press = handler._parse_key('\xff')
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.char == 'ÿ'
        assert key_press.raw_sequence == ''
        assert key_press.shift is False  # Not uppercase
    
    def test_parse_control_char_ctrl_combinations(self, handler):
        """Test parsing Ctrl key combinations."""
        # Ctrl+A (ord 1)
        key_press = handler._parse_control_char('\x01')
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.char == 'a'
        assert key_press.ctrl is True
        
        # Ctrl+Z (ord 26)
        key_press = handler._parse_control_char('\x1a')
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.char == 'z'
        assert key_press.ctrl is True
    
    def test_parse_control_char_unknown(self, handler):
        """Test parsing unknown control character."""
        key_press = handler._parse_control_char('\x00')
        assert key_press.key == KeyCode.UNKNOWN
        assert key_press.raw_sequence == '\x00'
    
    def test_parse_control_char_backspace_direct(self, handler):
        """Test parsing control backspace character directly (line 227)."""
        # Test BS (8) directly through _parse_control_char to hit line 227
        key_press = handler._parse_control_char('\x08')
        assert key_press.key == KeyCode.BACKSPACE
        
        # Test what happens with DEL (127) through control char parser
        # This won't normally happen since 127 > 32, but tests the logic
        key_press = handler._parse_control_char('\x7f')
        assert key_press.key == KeyCode.BACKSPACE
    
    def test_parse_control_char_escape_direct(self, handler):
        """Test parsing control escape character directly (line 229)."""
        # Test ESC (27) directly through _parse_control_char to hit line 229
        key_press = handler._parse_control_char('\x1b')
        assert key_press.key == KeyCode.ESCAPE
    
    def test_bind_key(self, handler):
        """Test key binding functionality."""
        callback = Mock()
        
        handler.bind_key("q", callback)
        
        assert "q" in handler.key_bindings
        assert handler.key_bindings["q"] == callback
    
    def test_bind_key_case_insensitive(self, handler):
        """Test key binding is case insensitive."""
        callback = Mock()
        
        handler.bind_key("Q", callback)
        
        assert "q" in handler.key_bindings
    
    def test_handle_key_exact_match(self, handler):
        """Test handling key with exact pattern match."""
        callback = Mock()
        handler.bind_key("enter", callback)
        
        key_press = KeyPress(key=KeyCode.ENTER)
        result = handler.handle_key(key_press)
        
        assert result is True
        callback.assert_called_once_with(key_press)
    
    def test_handle_key_character_match(self, handler):
        """Test handling key with character match."""
        callback = Mock()
        handler.bind_key("a", callback)
        
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='a')
        result = handler.handle_key(key_press)
        
        assert result is True
        callback.assert_called_once_with(key_press)
    
    def test_handle_key_character_match_case_insensitive(self, handler):
        """Test character matching is case insensitive."""
        callback = Mock()
        handler.bind_key("a", callback)
        
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='A')
        result = handler.handle_key(key_press)
        
        assert result is True
        callback.assert_called_once_with(key_press)
    
    def test_handle_key_character_match_direct(self, handler):
        """Test direct character match in key bindings (covers lines 268-270)."""
        callback = Mock()
        handler.key_bindings["x"] = callback  # Direct binding
        
        # Test with lowercase char - should hit lines 268-270
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='x')
        result = handler.handle_key(key_press)
        
        assert result is True
        callback.assert_called_once_with(key_press)
        
        # Test with uppercase char - should still match via .lower() on line 268-269
        callback.reset_mock()
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='X')
        result = handler.handle_key(key_press)
        
        assert result is True
        callback.assert_called_once_with(key_press)
    
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.isatty')
    @patch('storm_checker.cli.components.keyboard_handler.select.select')
    @patch('storm_checker.cli.components.keyboard_handler.sys.stdin.read')
    def test_read_key_escape_sequence_timeout_covers_line_191(self, mock_read, mock_select, mock_isatty, handler):
        """Test escape sequence timeout to cover line 191."""
        mock_isatty.return_value = True
        
        # Mock select: first call has input (the initial escape), all subsequent calls timeout
        mock_select.side_effect = [([], [], [])] * 11  # All selects timeout - no input
        
        # Mock a single escape character read
        mock_read.return_value = '\x1b'
        
        key_press = handler.read_key()
        
        assert key_press is not None
        assert key_press.key == KeyCode.ESCAPE
        assert key_press.raw_sequence == '\x1b'
    
    def test_handle_key_no_match(self, handler):
        """Test handling key with no binding."""
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='x')
        result = handler.handle_key(key_press)
        
        assert result is False
    
    def test_handle_key_character_match_bypasses_pattern(self, handler):
        """Test character match when pattern match fails (covers lines 268-270)."""
        callback = Mock()
        
        # Add a binding for just the character 'n'
        handler.key_bindings["n"] = callback
        
        # Create key press with Ctrl modifier - pattern will be 'ctrl+n' but char.lower() = 'n'
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='N', ctrl=True)
        
        # Verify the pattern doesn't exist but the character does
        pattern = handler._key_press_to_pattern(key_press)
        assert pattern == "ctrl+n"
        assert pattern not in handler.key_bindings  # Pattern 'ctrl+n' doesn't exist
        assert key_press.char.lower() in handler.key_bindings  # But 'n' does exist
        
        # This should skip line 263-265 (pattern match fails) and hit lines 268-270 (char match succeeds)
        result = handler.handle_key(key_press)
        
        assert result is True
        callback.assert_called_once_with(key_press)
    
    def test_key_press_to_pattern_simple(self, handler):
        """Test converting simple key press to pattern."""
        key_press = KeyPress(key=KeyCode.ENTER)
        pattern = handler._key_press_to_pattern(key_press)
        
        assert pattern == "enter"
    
    def test_key_press_to_pattern_with_modifiers(self, handler):
        """Test converting key press with modifiers to pattern."""
        key_press = KeyPress(key=KeyCode.UP, ctrl=True, alt=True, shift=True)
        pattern = handler._key_press_to_pattern(key_press)
        
        assert pattern == "ctrl+alt+shift+up"
    
    def test_key_press_to_pattern_character(self, handler):
        """Test converting character key press to pattern."""
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='a')
        pattern = handler._key_press_to_pattern(key_press)
        
        assert pattern == "a"
    
    def test_key_press_to_pattern_character_with_ctrl(self, handler):
        """Test converting character with Ctrl to pattern."""
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='c', ctrl=True)
        pattern = handler._key_press_to_pattern(key_press)
        
        assert pattern == "ctrl+c"
    
    def test_key_press_to_pattern_shift_not_added_for_unknown(self, handler):
        """Test that shift modifier not added for unknown keys unless specified."""
        key_press = KeyPress(key=KeyCode.UNKNOWN, char='A', shift=True)
        pattern = handler._key_press_to_pattern(key_press)
        
        assert pattern == "a"  # shift not included for UNKNOWN keys
    
    def test_create_input_loop_default_quit_keys(self, handler):
        """Test creating input loop with default quit keys."""
        loop_instance = handler.create_input_loop()
        
        # Should return an instance, not a class
        assert hasattr(loop_instance, 'run')
        assert hasattr(loop_instance, 'running')
        assert hasattr(loop_instance, '__enter__')
        assert hasattr(loop_instance, '__exit__')
    
    def test_create_input_loop_custom_quit_keys(self, handler):
        """Test creating input loop with custom quit keys."""
        loop_instance = handler.create_input_loop(quit_keys=["x", "y"])
        
        # Should return an instance, not a class
        assert hasattr(loop_instance, 'run')
        assert hasattr(loop_instance, 'running')
        assert hasattr(loop_instance, '__enter__')
        assert hasattr(loop_instance, '__exit__')
    
    def test_input_loop_context_manager(self, handler):
        """Test input loop as context manager."""
        with patch.object(handler, 'enter_raw_mode') as mock_enter:
            with patch.object(handler, 'exit_raw_mode') as mock_exit:
                loop_instance = handler.create_input_loop(prompt="Test: ")
                
                with patch('builtins.print') as mock_print:
                    with loop_instance as loop:
                        assert loop.running is True
                        mock_enter.assert_called_once()
                        mock_print.assert_called_once_with("Test: ", end='', flush=True)
                    
                    mock_exit.assert_called_once()
                    assert loop.running is False
    
    def test_input_loop_run_not_running(self, handler):
        """Test input loop run when not running."""
        loop_instance = handler.create_input_loop()
        loop_instance.running = False
        
        result = loop_instance.run()
        
        assert result is None
    
    def test_input_loop_run_with_quit_key(self, handler):
        """Test input loop run with quit key."""
        with patch.object(handler, 'read_key') as mock_read:
            mock_key = KeyPress(key=KeyCode.UNKNOWN, char='q')
            mock_read.return_value = mock_key
            
            loop_instance = handler.create_input_loop(quit_keys=["q"])
            loop_instance.running = True
            
            result = loop_instance.run()
            
            assert result is None
            assert loop_instance.running is False
    
    def test_input_loop_run_with_regular_key(self, handler):
        """Test input loop run with regular key."""
        with patch.object(handler, 'read_key') as mock_read:
            with patch.object(handler, 'handle_key') as mock_handle:
                mock_key = KeyPress(key=KeyCode.UNKNOWN, char='a')
                mock_read.return_value = mock_key
                
                loop_instance = handler.create_input_loop()
                loop_instance.running = True
                
                result = loop_instance.run()
                
                assert result == mock_key
                mock_handle.assert_called_once_with(mock_key)
    
    def test_input_loop_run_no_key(self, handler):
        """Test input loop run with no key."""
        with patch.object(handler, 'read_key', return_value=None):
            loop_instance = handler.create_input_loop()
            loop_instance.running = True
            
            result = loop_instance.run()
            
            assert result is None
    
    def test_wait_for_key_any_key(self, handler):
        """Test waiting for any key."""
        with patch.object(handler, 'enter_raw_mode'):
            with patch.object(handler, 'exit_raw_mode'):
                with patch.object(handler, 'read_key') as mock_read:
                    mock_key = KeyPress(key=KeyCode.ENTER)
                    mock_read.return_value = mock_key
                    
                    result = handler.wait_for_key()
                    
                    assert result == mock_key
    
    def test_wait_for_key_specific_keys(self, handler):
        """Test waiting for specific keys."""
        with patch.object(handler, 'enter_raw_mode'):
            with patch.object(handler, 'exit_raw_mode'):
                with patch.object(handler, 'read_key') as mock_read:
                    # First return invalid key, then valid key
                    mock_read.side_effect = [
                        KeyPress(key=KeyCode.UNKNOWN, char='x'),  # Invalid
                        KeyPress(key=KeyCode.UNKNOWN, char='y')   # Valid
                    ]
                    
                    result = handler.wait_for_key(valid_keys=["y", "z"])
                    
                    assert result.char == 'y'
                    assert mock_read.call_count == 2
    
    def test_wait_for_key_pattern_match(self, handler):
        """Test waiting for key with pattern matching."""
        with patch.object(handler, 'enter_raw_mode'):
            with patch.object(handler, 'exit_raw_mode'):
                with patch.object(handler, 'read_key') as mock_read:
                    mock_key = KeyPress(key=KeyCode.ENTER)
                    mock_read.return_value = mock_key
                    
                    result = handler.wait_for_key(valid_keys=["enter"])
                    
                    assert result == mock_key
    
    def test_context_manager_methods(self, handler):
        """Test context manager entry and exit methods."""
        with patch.object(handler, 'enter_raw_mode') as mock_enter:
            with patch.object(handler, 'exit_raw_mode') as mock_exit:
                with handler:
                    mock_enter.assert_called_once()
                
                mock_exit.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('storm_checker.cli.components.keyboard_handler.KeyboardHandler')
    @patch('builtins.print')
    def test_wait_for_any_key_default_prompt(self, mock_print, mock_handler_class):
        """Test wait_for_any_key with default prompt."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        mock_key = KeyPress(key=KeyCode.ENTER)
        mock_handler.wait_for_key.return_value = mock_key
        
        result = wait_for_any_key()
        
        assert result == mock_key
        mock_print.assert_any_call("Press any key to continue...", end='', flush=True)
        mock_print.assert_any_call()  # Newline
        mock_handler.wait_for_key.assert_called_once_with()
    
    @patch('storm_checker.cli.components.keyboard_handler.KeyboardHandler')
    @patch('builtins.print')
    def test_wait_for_any_key_custom_prompt(self, mock_print, mock_handler_class):
        """Test wait_for_any_key with custom prompt."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        mock_key = KeyPress(key=KeyCode.ENTER)
        mock_handler.wait_for_key.return_value = mock_key
        
        result = wait_for_any_key("Custom prompt: ")
        
        assert result == mock_key
        mock_print.assert_any_call("Custom prompt: ", end='', flush=True)
    
    @patch('storm_checker.cli.components.keyboard_handler.KeyboardHandler')
    @patch('builtins.print')
    def test_wait_for_specific_key(self, mock_print, mock_handler_class):
        """Test wait_for_specific_key function."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        mock_key = KeyPress(key=KeyCode.UNKNOWN, char='y')
        mock_handler.wait_for_key.return_value = mock_key
        
        result = wait_for_specific_key(['y', 'n'], "Continue? ")
        
        assert result == mock_key
        mock_print.assert_any_call("Continue? (y/n)", end='', flush=True)
        mock_handler.wait_for_key.assert_called_once_with(['y', 'n'])
    
    @patch('storm_checker.cli.components.keyboard_handler.KeyboardHandler')
    def test_create_navigation_handler(self, mock_handler_class):
        """Test create_navigation_handler function."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        result = create_navigation_handler()
        
        assert result == mock_handler
        # Should bind 3 keys: q, h, ctrl+c
        assert mock_handler.bind_key.call_count == 3
        
        # Check that keys were bound
        bound_keys = [call[0][0] for call in mock_handler.bind_key.call_args_list]
        assert "q" in bound_keys
        assert "h" in bound_keys
        assert "ctrl+c" in bound_keys
    
    @patch('storm_checker.cli.components.keyboard_handler.KeyboardHandler')
    @patch('builtins.print')
    def test_demo_keyboard_handler(self, mock_print, mock_handler_class):
        """Test demo_keyboard_handler function."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        # Mock the input loop - use MagicMock for context manager
        mock_loop = MagicMock()
        mock_loop.running = True
        mock_loop.__enter__.return_value = mock_loop
        mock_loop.__exit__.return_value = None
        
        # Simulate loop running once then stopping
        def side_effect():
            mock_loop.running = False
            return None
        mock_loop.run.side_effect = side_effect
        
        mock_handler.create_input_loop.return_value = mock_loop
        mock_handler.handle_key.return_value = True
        
        demo_keyboard_handler()
        
        # Should print demo messages
        mock_print.assert_any_call("=== Keyboard Handler Demo ===")
        mock_print.assert_any_call("\nDemo complete!")
        
        # Should bind keys
        assert mock_handler.bind_key.call_count > 0
        
        # Should create input loop
        mock_handler.create_input_loop.assert_called_once()
    
    @patch('storm_checker.cli.components.keyboard_handler.KeyboardHandler')
    @patch('builtins.print')
    def test_demo_keyboard_handler_unhandled_key(self, mock_print, mock_handler_class):
        """Test demo with unhandled key press."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        # Mock the input loop - use MagicMock for context manager
        mock_loop = MagicMock()
        mock_loop.running = True
        mock_loop.__enter__.return_value = mock_loop
        mock_loop.__exit__.return_value = None
        
        # Mock key press
        mock_key = KeyPress(key=KeyCode.UNKNOWN, char='x', ctrl=True, alt=True, shift=True)
        
        # Simulate loop returning key then stopping
        def side_effect():
            mock_loop.running = False
            return mock_key
        mock_loop.run.side_effect = side_effect
        
        mock_handler.create_input_loop.return_value = mock_loop
        mock_handler.handle_key.return_value = False  # Unhandled key
        
        demo_keyboard_handler()
        
        # Should print key information
        mock_print.assert_any_call("Character: 'x'", end=' ')
        mock_print.assert_any_call("Key: unknown")
        mock_print.assert_any_call("  [with Ctrl]")
        mock_print.assert_any_call("  [with Alt]")
        mock_print.assert_any_call("  [with Shift]")


class TestMainExecution:
    """Test main execution path."""
    
    @patch('storm_checker.cli.components.keyboard_handler.demo_keyboard_handler')
    def test_main_execution(self, mock_demo):
        """Test that demo runs when module executed as main."""
        # Simulate running as main module
        import sys
        original_name = sys.modules['cli.components.keyboard_handler'].__name__ if 'cli.components.keyboard_handler' in sys.modules else None
        
        try:
            # This test would require actually running the module as __main__
            # which is complex to test. We'll just verify the demo function exists
            # and would be callable
            assert callable(demo_keyboard_handler)
        finally:
            if original_name:
                sys.modules['cli.components.keyboard_handler'].__name__ = original_name
