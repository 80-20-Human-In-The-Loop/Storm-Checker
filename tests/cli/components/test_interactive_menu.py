"""
Comprehensive Tests for Interactive Menu Component
================================================
Tests for the InteractiveMenu class with full coverage of all functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

from storm_checker.cli.components.interactive_menu import (
    InteractiveMenu,
    MenuItem,
    MenuItemType,
    demo_interactive_menu
)
from storm_checker.cli.components.keyboard_handler import KeyPress, KeyCode


class TestMenuItem:
    """Test the MenuItem dataclass."""
    
    def test_menu_item_creation_defaults(self):
        """Test creating a MenuItem with defaults."""
        item = MenuItem(text="Test Item")
        
        assert item.text == "Test Item"
        assert item.value is None
        assert item.type == MenuItemType.NORMAL
        assert item.description is None
        assert item.metadata is None
        assert item.icon is None
        assert item.color is None
    
    def test_menu_item_creation_all_fields(self):
        """Test creating a MenuItem with all fields specified."""
        metadata = {"difficulty": 3, "completed": True}
        item = MenuItem(
            text="Advanced Tutorial",
            value="advanced",
            type=MenuItemType.NORMAL,
            description="Advanced concepts",
            metadata=metadata,
            icon="🚀",
            color="blue"
        )
        
        assert item.text == "Advanced Tutorial"
        assert item.value == "advanced"
        assert item.type == MenuItemType.NORMAL
        assert item.description == "Advanced concepts"
        assert item.metadata == metadata
        assert item.icon == "🚀"
        assert item.color == "blue"
    
    def test_menu_item_types(self):
        """Test different menu item types."""
        normal = MenuItem("Normal", type=MenuItemType.NORMAL)
        header = MenuItem("Header", type=MenuItemType.HEADER)
        separator = MenuItem("", type=MenuItemType.SEPARATOR)
        
        assert normal.type == MenuItemType.NORMAL
        assert header.type == MenuItemType.HEADER
        assert separator.type == MenuItemType.SEPARATOR


class TestInteractiveMenu:
    """Test the InteractiveMenu class."""
    
    def _setup_keyboard_mock(self, mock_kh_class, mock_menu, key_sequence):
        """Helper to set up keyboard handler mock."""
        mock_loop = Mock()
        mock_loop.running = True
        
        # Create a context manager mock
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=mock_loop)
        context_manager.__exit__ = Mock(return_value=False)
        
        mock_kh_class.return_value.create_input_loop.return_value = context_manager
        mock_menu.keyboard_handler = mock_kh_class.return_value
        
        # Set up key sequence
        call_count = [0]
        def mock_run():
            call_count[0] += 1
            if call_count[0] <= len(key_sequence):
                return key_sequence[call_count[0] - 1]
            else:
                mock_loop.running = False
                return None
        
        mock_loop.run = Mock(side_effect=mock_run)
        return mock_loop
    
    @pytest.fixture
    def mock_menu(self):
        """Create a menu with mocked dependencies."""
        with patch('storm_checker.cli.components.interactive_menu.KeyboardHandler') as mock_kh:
            with patch('storm_checker.cli.components.interactive_menu.RichTerminal') as mock_rt:
                with patch('storm_checker.cli.components.interactive_menu.BufferedRenderer') as mock_br:
                    menu = InteractiveMenu(title="Test Menu", subtitle="Test Subtitle")
                    
                    # Set up mocks
                    menu.keyboard_handler = mock_kh.return_value
                    menu.rich_terminal = mock_rt.return_value
                    menu.buffered_renderer = mock_br.return_value
                    
                    # Ensure get_buffer returns string instead of MagicMock
                    menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
                    
                    yield menu
    
    def test_menu_initialization_defaults(self):
        """Test menu initialization with default parameters."""
        with patch('storm_checker.cli.components.interactive_menu.KeyboardHandler'):
            with patch('storm_checker.cli.components.interactive_menu.RichTerminal'):
                with patch('storm_checker.cli.components.interactive_menu.BufferedRenderer'):
                    menu = InteractiveMenu()
                    
                    assert menu.title == "Menu"
                    assert menu.subtitle is None
                    assert menu.items == []
                    assert menu.selected_index == 0
                    assert menu.on_select is None
                    assert menu.show_instructions == True
                    assert menu.custom_colors == {}
    
    def test_menu_initialization_custom(self):
        """Test menu initialization with custom parameters."""
        with patch('storm_checker.cli.components.interactive_menu.KeyboardHandler'):
            with patch('storm_checker.cli.components.interactive_menu.RichTerminal'):
                with patch('storm_checker.cli.components.interactive_menu.BufferedRenderer'):
                    menu = InteractiveMenu(
                        title="Custom Menu",
                        subtitle="Custom Subtitle", 
                        use_rich=False,
                        persistent_mode=False
                    )
                    
                    assert menu.title == "Custom Menu"
                    assert menu.subtitle == "Custom Subtitle"
    
    def test_add_item_minimal(self, mock_menu):
        """Test adding a menu item with minimal parameters."""
        mock_menu.add_item("Test Item")
        
        assert len(mock_menu.items) == 1
        item = mock_menu.items[0]
        assert item.text == "Test Item"
        assert item.value == "Test Item"  # Defaults to text
        assert item.type == MenuItemType.NORMAL
        assert item.description is None
        assert item.metadata == {}
        assert item.icon is None
        assert item.color is None
    
    def test_add_item_full(self, mock_menu):
        """Test adding a menu item with all parameters."""
        metadata = {"difficulty": 2, "time": 15}
        mock_menu.add_item(
            text="Full Item",
            value="full_item",
            description="Full description",
            icon="🔥",
            color="red",
            metadata=metadata
        )
        
        assert len(mock_menu.items) == 1
        item = mock_menu.items[0]
        assert item.text == "Full Item"
        assert item.value == "full_item"
        assert item.description == "Full description"
        assert item.icon == "🔥"
        assert item.color == "red"
        assert item.metadata == metadata
    
    def test_add_header(self, mock_menu):
        """Test adding a header item."""
        mock_menu.add_header("Section Header", color="blue")
        
        assert len(mock_menu.items) == 1
        item = mock_menu.items[0]
        assert item.text == "Section Header"
        assert item.type == MenuItemType.HEADER
        assert item.color == "blue"
    
    def test_add_separator(self, mock_menu):
        """Test adding a separator item."""
        mock_menu.add_separator()
        
        assert len(mock_menu.items) == 1
        item = mock_menu.items[0]
        assert item.text == ""
        assert item.type == MenuItemType.SEPARATOR
    
    def test_set_custom_colors(self, mock_menu):
        """Test setting custom colors."""
        colors = {"primary": "#123456", "secondary": "#abcdef"}
        mock_menu.set_custom_colors(colors)
        
        assert mock_menu.custom_colors == colors
    
    def test_get_selectable_indices_empty(self, mock_menu):
        """Test getting selectable indices with no items."""
        indices = mock_menu._get_selectable_indices()
        assert indices == []
    
    def test_get_selectable_indices_mixed(self, mock_menu):
        """Test getting selectable indices with mixed item types."""
        mock_menu.add_header("Header")          # Index 0 - not selectable
        mock_menu.add_item("Item 1")            # Index 1 - selectable
        mock_menu.add_separator()               # Index 2 - not selectable
        mock_menu.add_item("Item 2")            # Index 3 - selectable
        mock_menu.add_header("Another Header")  # Index 4 - not selectable
        mock_menu.add_item("Item 3")            # Index 5 - selectable
        
        indices = mock_menu._get_selectable_indices()
        assert indices == [1, 3, 5]
    
    def test_move_selection_no_selectable(self, mock_menu):
        """Test moving selection when no selectable items exist."""
        mock_menu.add_header("Header Only")
        mock_menu.selected_index = 0
        
        mock_menu._move_selection(1)
        # Should remain unchanged
        assert mock_menu.selected_index == 0
    
    def test_move_selection_down(self, mock_menu):
        """Test moving selection down."""
        mock_menu.add_item("Item 1")  # Index 0
        mock_menu.add_item("Item 2")  # Index 1
        mock_menu.add_item("Item 3")  # Index 2
        mock_menu.selected_index = 0
        
        mock_menu._move_selection(1)
        assert mock_menu.selected_index == 1
        
        mock_menu._move_selection(1)
        assert mock_menu.selected_index == 2
        
        # Should not move beyond bounds
        mock_menu._move_selection(1)
        assert mock_menu.selected_index == 2
    
    def test_move_selection_up(self, mock_menu):
        """Test moving selection up."""
        mock_menu.add_item("Item 1")  # Index 0
        mock_menu.add_item("Item 2")  # Index 1
        mock_menu.add_item("Item 3")  # Index 2
        mock_menu.selected_index = 2
        
        mock_menu._move_selection(-1)
        assert mock_menu.selected_index == 1
        
        mock_menu._move_selection(-1)
        assert mock_menu.selected_index == 0
        
        # Should not move beyond bounds
        mock_menu._move_selection(-1)
        assert mock_menu.selected_index == 0
    
    def test_move_selection_invalid_current(self, mock_menu):
        """Test moving selection when current selection is invalid."""
        mock_menu.add_item("Item 1")  # Index 0
        mock_menu.add_item("Item 2")  # Index 1
        mock_menu.add_separator()     # Index 2
        mock_menu.selected_index = 2  # Invalid (separator)
        
        mock_menu._move_selection(1)
        # Should reset to first selectable item
        assert mock_menu.selected_index == 0
    
    def test_move_selection_with_mixed_types(self, mock_menu):
        """Test moving selection with mixed item types (only selectable items)."""
        mock_menu.add_header("Header")    # Index 0 - not selectable
        mock_menu.add_item("Item 1")      # Index 1 - selectable
        mock_menu.add_separator()         # Index 2 - not selectable  
        mock_menu.add_item("Item 2")      # Index 3 - selectable
        mock_menu.selected_index = 1
        
        mock_menu._move_selection(1)
        assert mock_menu.selected_index == 3
        
        mock_menu._move_selection(-1)
        assert mock_menu.selected_index == 1
    
    def test_strip_markup(self, mock_menu):
        """Test stripping Rich markup from text."""
        text_with_markup = "[bold red]Hello[/bold red] [green]World[/green]"
        clean_text = mock_menu._strip_markup(text_with_markup)
        assert clean_text == "Hello World"
    
    def test_render_menu_basic(self, mock_menu):
        """Test basic menu rendering."""
        mock_menu.add_item("Test Item")
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        result = mock_menu._render_menu()
        
        # Verify the rendering methods were called
        mock_menu.rich_terminal.print_panel.assert_called()
        mock_menu.rich_terminal.print.assert_called()
        assert result == "mocked_buffer"
    
    def test_render_menu_no_title(self, mock_menu):
        """Test menu rendering without title."""
        mock_menu.title = ""
        mock_menu.add_item("Test Item")
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        result = mock_menu._render_menu()
        
        # Title panel should not be called
        mock_menu.rich_terminal.print_panel.assert_not_called()
        mock_menu.rich_terminal.print.assert_called()
    
    def test_render_menu_with_headers_and_separators(self, mock_menu):
        """Test menu rendering with headers and separators."""
        mock_menu.add_header("Section 1")
        mock_menu.add_item("Item 1")
        mock_menu.add_separator()
        mock_menu.add_item("Item 2")
        mock_menu.selected_index = 1
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        result = mock_menu._render_menu()
        
        mock_menu.rich_terminal.print.assert_called()
        assert result == "mocked_buffer"
    
    def test_render_menu_with_metadata(self, mock_menu):
        """Test menu rendering with item metadata."""
        mock_menu.add_item(
            "Advanced Item",
            metadata={
                "completed": True,
                "difficulty": 3,
                "time": 25
            }
        )
        mock_menu.selected_index = 0
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        result = mock_menu._render_menu()
        
        mock_menu.rich_terminal.print.assert_called()
        # Check that the print call includes metadata indicators
        call_args = mock_menu.rich_terminal.print.call_args[0][0]
        assert "✅" in call_args  # completed indicator
        assert "Level 3" in call_args  # difficulty indicator
        assert "25 min" in call_args  # time indicator
    
    def test_render_menu_with_icon(self, mock_menu):
        """Test menu rendering with item icon."""
        mock_menu.add_item("Item with icon", icon="🚀")
        mock_menu.selected_index = 0
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        result = mock_menu._render_menu()
        
        mock_menu.rich_terminal.print.assert_called()
        call_args = mock_menu.rich_terminal.print.call_args[0][0]
        assert "🚀" in call_args  # icon should be present
    
    def test_render_menu_selected_with_description(self, mock_menu):
        """Test menu rendering with selected item having description."""
        mock_menu.add_item("Item with description", description="This is a test description")
        mock_menu.selected_index = 0
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        result = mock_menu._render_menu()
        
        mock_menu.rich_terminal.print.assert_called()
        call_args = mock_menu.rich_terminal.print.call_args[0][0]
        assert "This is a test description" in call_args
    
    def test_render_menu_without_rich(self, mock_menu):
        """Test menu rendering without Rich formatting."""
        mock_menu.rich_terminal.use_rich = False
        mock_menu.add_item("Test Item")
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        with patch('builtins.print') as mock_print:
            result = mock_menu._render_menu()
            
            # Should use print instead of rich_terminal.print
            mock_print.assert_called()
            mock_menu.rich_terminal.print.assert_not_called()
    
    def test_render_menu_custom_colors(self, mock_menu):
        """Test menu rendering with custom colors."""
        mock_menu.set_custom_colors({
            'primary': '#123456',
            'selection_bg': '#abcdef',
            'selection_fg': '#fedcba',
            'header': '#555555',
            'normal': '#888888',
            'description': '#cccccc'
        })
        mock_menu.add_header("Custom Header")
        mock_menu.add_item("Custom Item", description="Custom description")
        mock_menu.selected_index = 1
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        result = mock_menu._render_menu()
        
        mock_menu.rich_terminal.print.assert_called()
        # Verify custom colors are used in the output
        call_args = mock_menu.rich_terminal.print.call_args[0][0]
        assert "#abcdef" in call_args  # selection background
        assert "#fedcba" in call_args  # selection foreground
    
    def test_render_menu_no_instructions(self, mock_menu):
        """Test menu rendering without instructions."""
        mock_menu.show_instructions = False
        mock_menu.add_item("Test Item")
        mock_menu.buffered_renderer.get_buffer.return_value = "mocked_buffer"
        
        result = mock_menu._render_menu()
        
        call_args = mock_menu.rich_terminal.print.call_args[0][0]
        assert "Navigate with ↑↓ arrows" not in call_args
    
    def test_run_no_selectable_items(self, mock_menu):
        """Test running menu with no selectable items."""
        mock_menu.add_header("Header Only")
        mock_menu.add_separator()
        
        result = mock_menu.run()
        
        assert result is None
        mock_menu.rich_terminal.print.assert_called_with(
            "[red]No selectable items in menu![/red]", markup=True
        )
    
    @patch('storm_checker.cli.components.interactive_menu.KeyboardHandler')
    def test_run_select_item(self, mock_kh_class, mock_menu):
        """Test running menu and selecting an item."""
        mock_menu.add_item("Test Item", value="test_value")
        
        # Create a mock KeyPress with the value the menu expects
        enter_key = Mock()
        enter_key.key = Mock()
        enter_key.key.value = "ENTER"
        enter_key.char = None
        
        self._setup_keyboard_mock(mock_kh_class, mock_menu, [enter_key])
        
        result = mock_menu.run()
        
        assert result is not None
        assert result.text == "Test Item"
        assert result.value == "test_value"
    
    @patch('storm_checker.cli.components.interactive_menu.KeyboardHandler')
    def test_run_navigate_and_select(self, mock_kh_class, mock_menu):
        """Test running menu with navigation then selection."""
        mock_menu.add_item("Item 1", value="item1")
        mock_menu.add_item("Item 2", value="item2")
        
        down_key = Mock()
        down_key.key = Mock()
        down_key.key.value = "DOWN"
        down_key.char = None
        
        enter_key = Mock()
        enter_key.key = Mock()
        enter_key.key.value = "ENTER"
        enter_key.char = None
        
        self._setup_keyboard_mock(mock_kh_class, mock_menu, [down_key, enter_key])
        
        result = mock_menu.run()
        
        assert result is not None
        assert result.text == "Item 2"
        assert result.value == "item2"
    
    @patch('storm_checker.cli.components.interactive_menu.KeyboardHandler')
    def test_run_quit_with_q(self, mock_kh_class, mock_menu):
        """Test running menu and quitting with 'q'."""
        mock_menu.add_item("Test Item")
        
        q_key = Mock()
        q_key.key = Mock()
        q_key.key.value = "UNKNOWN"
        q_key.char = 'q'
        
        self._setup_keyboard_mock(mock_kh_class, mock_menu, [q_key])
        
        result = mock_menu.run()
        
        assert result is None
    
    @patch('storm_checker.cli.components.interactive_menu.KeyboardHandler')
    def test_run_quit_with_escape(self, mock_kh_class, mock_menu):
        """Test running menu and quitting with Escape."""
        mock_menu.add_item("Test Item")
        
        esc_key = Mock()
        esc_key.key = Mock()
        esc_key.key.value = "ESCAPE"
        esc_key.char = None
        
        self._setup_keyboard_mock(mock_kh_class, mock_menu, [esc_key])
        
        result = mock_menu.run()
        
        assert result is None
    
    @patch('storm_checker.cli.components.interactive_menu.KeyboardHandler')
    def test_run_with_callback(self, mock_kh_class, mock_menu):
        """Test running menu with on_select callback."""
        mock_menu.add_item("Test Item", value="test_value")
        
        # Set up callback
        callback = Mock()
        mock_menu.on_select = callback
        
        enter_key = Mock()
        enter_key.key = Mock()
        enter_key.key.value = "ENTER"
        enter_key.char = None
        
        self._setup_keyboard_mock(mock_kh_class, mock_menu, [enter_key])
        
        result = mock_menu.run()
        
        # Verify callback was called
        callback.assert_called_once()
        assert callback.call_args[0][0].text == "Test Item"
    
    @patch('storm_checker.cli.components.interactive_menu.KeyboardHandler')
    def test_run_navigation_up_down(self, mock_kh_class, mock_menu):
        """Test running menu with up and down navigation."""
        mock_menu.add_item("Item 1")
        mock_menu.add_item("Item 2")
        mock_menu.add_item("Item 3")
        
        up_key = Mock()
        up_key.key = Mock()
        up_key.key.value = "UP"
        up_key.char = None
        
        down_key = Mock()
        down_key.key = Mock()
        down_key.key.value = "DOWN"
        down_key.char = None
        
        enter_key = Mock()
        enter_key.key = Mock()
        enter_key.key.value = "ENTER"
        enter_key.char = None
        
        # Navigate: down, down, up, enter -> should select Item 2
        key_sequence = [down_key, down_key, up_key, enter_key]
        self._setup_keyboard_mock(mock_kh_class, mock_menu, key_sequence)
        
        result = mock_menu.run()
        
        # Should have navigated down twice, up once, then selected Item 2
        assert result is not None
        assert result.text == "Item 2"
    
    def test_cleanup(self, mock_menu):
        """Test cleanup method."""
        mock_menu.cleanup()
        mock_menu.rich_terminal.cleanup.assert_called_once()
    
    def test_context_manager(self, mock_menu):
        """Test context manager support."""
        with mock_menu as menu:
            assert menu is mock_menu
        
        mock_menu.rich_terminal.cleanup.assert_called_once()
        
    @patch('storm_checker.cli.components.interactive_menu.KeyboardHandler')
    def test_run_with_none_key_press(self, mock_kh_class, mock_menu):
        """Test running menu when key_press is None (should continue loop)."""
        mock_menu.add_item("Test Item")
        
        # Create key sequence with None in between to test continue path
        enter_key = Mock()
        enter_key.key = Mock()
        enter_key.key.value = "ENTER"
        enter_key.char = None
        
        # Mock loop that returns None first, then ENTER
        mock_loop = Mock()
        mock_loop.running = True
        
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=mock_loop)
        context_manager.__exit__ = Mock(return_value=False)
        
        mock_kh_class.return_value.create_input_loop.return_value = context_manager
        mock_menu.keyboard_handler = mock_kh_class.return_value
        
        call_count = [0]
        def mock_run():
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # This should trigger continue
            elif call_count[0] == 2:
                return enter_key
            else:
                mock_loop.running = False
                return None
        
        mock_loop.run = Mock(side_effect=mock_run)
        
        result = mock_menu.run()
        
        assert result is not None
        assert result.text == "Test Item"
    
    @patch('storm_checker.cli.components.interactive_menu.KeyboardHandler')
    def test_run_loop_end_fallback(self, mock_kh_class, mock_menu):
        """Test running menu when loop ends without return (fallback return None)."""
        mock_menu.add_item("Test Item")
        
        # Mock loop that ends without selecting anything
        mock_loop = Mock()
        mock_loop.running = True
        
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=mock_loop)
        context_manager.__exit__ = Mock(return_value=False)
        
        mock_kh_class.return_value.create_input_loop.return_value = context_manager
        mock_menu.keyboard_handler = mock_kh_class.return_value
        
        # Mock returns some unknown key then stops loop
        unknown_key = Mock()
        unknown_key.key = Mock()
        unknown_key.key.value = "UNKNOWN"
        unknown_key.char = "x"  # Not 'q' or 'Q'
        
        call_count = [0]
        def mock_run():
            call_count[0] += 1
            if call_count[0] == 1:
                return unknown_key
            else:
                mock_loop.running = False  # Loop ends
                return None
        
        mock_loop.run = Mock(side_effect=mock_run)
        
        result = mock_menu.run()
        
        # Should return None from fallback at end of method
        assert result is None


def test_demo_interactive_menu():
    """Test the demo function."""
    with patch('storm_checker.cli.colors.print_rich_header') as mock_header:
        with patch('storm_checker.cli.components.interactive_menu.InteractiveMenu') as mock_menu_class:
            mock_menu = Mock()
            mock_menu_class.return_value = mock_menu
            mock_menu.run.return_value = Mock(text="Test", value="test")
            
            with patch('builtins.print') as mock_print:
                demo_interactive_menu()
                
                # Verify demo was set up correctly
                mock_header.assert_called_once()
                mock_menu_class.assert_called_once()
                mock_menu.set_custom_colors.assert_called_once()
                mock_menu.add_header.assert_called()
                mock_menu.add_item.assert_called()
                mock_menu.add_separator.assert_called_once()
                mock_menu.run.assert_called_once()
                mock_print.assert_called()

def test_demo_interactive_menu_cancelled():
    """Test the demo function when menu is cancelled."""  
    with patch('storm_checker.cli.colors.print_rich_header'):
        with patch('storm_checker.cli.components.interactive_menu.InteractiveMenu') as mock_menu_class:
            mock_menu = Mock()
            mock_menu_class.return_value = mock_menu
            mock_menu.run.return_value = None  # Cancelled
            
            with patch('builtins.print') as mock_print:
                demo_interactive_menu()
                
                # Verify cancellation message was printed
                mock_print.assert_called_with("\n[yellow]Menu cancelled[/yellow]")