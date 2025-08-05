"""
Tests for Progress Bar Component
================================
Test progress bar rendering and functionality.
"""

import pytest
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from storm_checker.cli.components.progress_bar import ProgressBar, SpinnerBar
from storm_checker.cli.colors import THEME, PALETTE, RESET


class TestProgressBar:
    """Test ProgressBar class functionality."""
    
    def test_progress_bar_initialization(self):
        """Test ProgressBar object creation."""
        bar = ProgressBar()
        assert bar.width == 20
        assert bar.show_percentage == True
        assert bar.show_fraction == False
        
    def test_progress_bar_with_custom_params(self):
        """Test ProgressBar with custom parameters."""
        bar = ProgressBar(
            width=30,
            style="dots",
            color_filled="success",
            show_percentage=True,
            show_fraction=True
        )
        
        assert bar.width == 30
        assert bar.show_percentage == True
        assert bar.show_fraction == True
        assert bar.color_filled == THEME['success']
        
    def test_render_basic(self):
        """Test basic rendering."""
        bar = ProgressBar(width=20)
        result = bar.render(25, 100)
        
        # Should contain progress indication
        assert "[" in result and "]" in result
        assert "25%" in result
        
    def test_render_with_label(self):
        """Test rendering with label."""
        bar = ProgressBar(width=20)
        result = bar.render(50, 100, label="Loading", suffix="Please wait")
        
        assert "Loading" in result
        assert "Please wait" in result
        assert "50%" in result
        
    def test_render_blocks_style(self):
        """Test rendering with blocks style."""
        bar = ProgressBar(style="blocks", width=20)
        result = bar.render(50, 100)
        
        # Should contain filled and empty blocks
        assert "█" in result  # Filled blocks
        assert "░" in result  # Empty blocks
        assert "50%" in result  # Percentage
        
    def test_render_dots_style(self):
        """Test rendering with dots style."""
        bar = ProgressBar(style="dots", width=20)
        result = bar.render(50, 100)
        
        # Should contain filled and empty dots
        assert "●" in result  # Filled dots
        assert "○" in result  # Empty dots
        
    def test_render_arrows_style(self):
        """Test rendering with arrows style."""
        bar = ProgressBar(style="arrows", width=20)
        result = bar.render(50, 100)
        
        # Should contain arrows
        assert "━" in result or "─" in result
        
    def test_render_with_percentage(self):
        """Test rendering with percentage display."""
        bar = ProgressBar(show_percentage=True)
        result = bar.render(33, 100)
        
        assert "33%" in result
        
    def test_render_with_fraction(self):
        """Test rendering with fraction display."""
        bar = ProgressBar(show_fraction=True)
        result = bar.render(25, 100)
        
        assert "25/100" in result
        
    def test_render_complete(self):
        """Test rendering when complete."""
        bar = ProgressBar()
        result = bar.render(100, 100)
        
        # Should show 100%
        assert "100%" in result
        
    def test_render_empty(self):
        """Test rendering when empty."""
        bar = ProgressBar()
        result = bar.render(0, 100)
        
        # Should show 0%
        assert "0%" in result
        
    def test_color_in_output(self):
        """Test that color codes are included."""
        bar = ProgressBar(color_filled="success")
        result = bar.render(50, 100)
        
        assert str(THEME['success']) in result
        assert RESET in result
        
    def test_different_widths(self):
        """Test progress bars with different widths."""
        widths = [10, 20, 30]
        
        for width in widths:
            bar = ProgressBar(width=width)
            result = bar.render(50, 100)
            
            # Should contain progress bar
            assert "[" in result and "]" in result
            assert "50%" in result
            
    def test_partial_blocks(self):
        """Test partial block rendering for precise progress."""
        bar = ProgressBar(style="blocks", width=10)
        result = bar.render(33, 100)
        
        # Should contain both filled and empty blocks
        assert "█" in result or "▏" in result  # Filled or partial blocks
        assert "░" in result  # Empty blocks
        
    @pytest.mark.parametrize("progress,total,expected_pct", [
        (0, 100, "0%"),
        (25, 100, "25%"),
        (50, 100, "50%"),
        (75, 100, "75%"),
        (100, 100, "100%"),
    ])
    def test_various_progress_levels(self, progress, total, expected_pct):
        """Test various progress levels."""
        bar = ProgressBar()
        result = bar.render(progress, total)
        assert expected_pct in result
        
    def test_invalid_style_fallback(self):
        """Test fallback for invalid style."""
        bar = ProgressBar(style="invalid_style")
        result = bar.render(50, 100)
        
        # Should fallback to blocks style
        assert "█" in result or "░" in result
        
    def test_zero_total_handling(self):
        """Test handling of zero total (edge case)."""
        bar = ProgressBar()
        result = bar.render(0, 0)
        
        # Should not crash and show 0%
        assert "0%" in result


def test_animated_progress():
    """Test animated progress (simulated)."""
    bar = ProgressBar(show_percentage=True)
    
    # Simulate progress animation
    for i in range(0, 101, 20):
        result = bar.render(i, 100, label="Processing")
        assert f"{i}%" in result
        assert "Processing" in result


def test_multi_progress_bars():
    """Test multiple progress bars (common use case)."""
    bars = [
        ProgressBar(color_filled="primary"),
        ProgressBar(color_filled="success"),
        ProgressBar(color_filled="warning"),
    ]
    
    progresses = [25, 50, 75]
    
    for bar, progress in zip(bars, progresses):
        result = bar.render(progress, 100)
        assert f"{progress}%" in result


class TestSegmentedProgressBar:
    """Test segmented progress bar functionality."""
    
    def test_render_segmented_basic(self):
        """Test basic segmented rendering."""
        bar = ProgressBar(width=30)
        segments = [
            (25, "success"),    # 25% success
            (15, "warning"),    # 15% warning
            (10, "error"),      # 10% error
            (50, "info"),       # 50% remaining
        ]
        
        result = bar.render_segmented(segments, 40)
        
        # Should contain progress indication
        assert "[" in result and "]" in result
        assert "40%" in result
    
    def test_render_segmented_with_label(self):
        """Test segmented rendering with label."""
        bar = ProgressBar(width=40)
        segments = [(50, "success"), (50, "warning")]
        
        result = bar.render_segmented(segments, 75, label="Progress")
        
        assert "Progress" in result
        assert "75%" in result
    
    def test_render_segmented_empty(self):
        """Test segmented rendering with zero progress."""
        bar = ProgressBar(width=20)
        segments = [(100, "info")]
        
        result = bar.render_segmented(segments, 0)
        assert "0%" in result
    
    def test_render_segmented_complete(self):
        """Test segmented rendering when complete."""
        bar = ProgressBar(width=20)
        segments = [(50, "success"), (50, "info")]
        
        result = bar.render_segmented(segments, 100)
        assert "100%" in result
    
    def test_render_segmented_partial_segments(self):
        """Test segmented rendering with current position in a segment."""
        bar = ProgressBar(style="blocks", width=40)
        segments = [
            (25, "success"),  # 0-25
            (25, "warning"),  # 25-50
            (50, "info"),     # 50-100
        ]
        
        # Current at 35 (in the warning segment)
        result = bar.render_segmented(segments, 35)
        
        # Should show partial progress in second segment
        assert "35%" in result
        # Should have colors from success and warning segments
        assert str(THEME['success']) in result or str(THEME['warning']) in result
    
    def test_render_segmented_colors(self):
        """Test that segment colors are applied."""
        bar = ProgressBar(width=30)
        segments = [
            (30, "success"),
            (30, "warning"),
            (40, "error"),
        ]
        
        result = bar.render_segmented(segments, 60)
        
        # Should contain color codes for at least one segment
        assert str(THEME['success']) in result or str(THEME['warning']) in result or str(THEME['error']) in result
    
    def test_render_segmented_zero_total(self):
        """Test segmented rendering with zero total (edge case)."""
        bar = ProgressBar()
        segments = []
        
        result = bar.render_segmented(segments, 0)
        
        # Should not crash and show something reasonable
        assert "[" in result and "]" in result
        assert "0%" in result
    
    def test_render_segmented_narrow_segments(self):
        """Test segmented rendering with very narrow segments."""
        bar = ProgressBar(width=10)  # Very narrow
        segments = [
            (10, "success"),
            (10, "warning"),
            (10, "error"),
            (70, "info"),
        ]
        
        result = bar.render_segmented(segments, 50)
        
        # Should still render without crashing
        assert "50%" in result


class TestSpinnerBar:
    """Test SpinnerBar class functionality."""
    
    def test_spinner_initialization(self):
        """Test SpinnerBar object creation."""
        spinner = SpinnerBar()
        assert spinner.current_frame == 0
        assert len(spinner.frames) > 0
    
    def test_spinner_with_custom_style(self):
        """Test SpinnerBar with custom style."""
        spinner = SpinnerBar(style="line", color="warning")
        assert spinner.color == THEME['warning']
        assert spinner.frames == ["-", "\\", "|", "/"]
    
    def test_spinner_next_frame(self):
        """Test spinner animation frames."""
        spinner = SpinnerBar(style="dots")
        
        # Get initial frame
        frame1 = spinner.next()
        assert len(frame1) > 0
        
        # Get next frame
        frame2 = spinner.next()
        assert len(frame2) > 0
        
        # Frames should be different (unless very unlucky with cycle)
        # Let's get a few more to ensure we see different frames
        frames = [spinner.next() for _ in range(len(spinner.frames))]
        unique_frames = set(frames)
        assert len(unique_frames) > 1
    
    def test_spinner_frame_cycling(self):
        """Test that spinner cycles through all frames."""
        spinner = SpinnerBar(style="line")
        
        # Cycle through all frames
        frames = []
        for _ in range(len(spinner.frames)):
            frames.append(spinner.next())
        
        # Should have seen all unique frames
        # Remove ANSI codes for comparison
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_frames = [ansi_escape.sub('', f) for f in frames]
        
        assert set(clean_frames) == set(spinner.frames)
    
    def test_spinner_styles(self):
        """Test different spinner styles."""
        styles = ["dots", "line", "circle", "bounce", "blocks"]
        
        for style in styles:
            spinner = SpinnerBar(style=style)
            frame = spinner.next()
            
            # Should produce output
            assert len(frame) > 0
            # Should contain color codes
            assert RESET in frame
    
    def test_spinner_invalid_style(self):
        """Test spinner with invalid style falls back to dots."""
        spinner = SpinnerBar(style="invalid_style")
        
        # Should fall back to dots style
        assert spinner.frames == SpinnerBar.SPINNERS["dots"]
    
    def test_spinner_color_output(self):
        """Test that spinner includes color codes."""
        spinner = SpinnerBar(color="error")
        frame = spinner.next()
        
        assert str(THEME['error']) in frame
        assert RESET in frame


def test_demo_function(capsys):
    """Test the demo() function runs without errors."""
    from unittest.mock import patch
    
    # Mock time.sleep to be instant - this avoids the 9+ second delay
    with patch('time.sleep'):
        from cli.components.progress_bar import demo
        
        # Run the demo (sleeps are mocked so it's instant)
        demo()
    
    # Capture output
    captured = capsys.readouterr()
    
    # Check that it produced output
    assert len(captured.out) > 0
    assert "Storm-Checker Progress Bar Demo" in captured.out
    assert "Basic Progress Bars:" in captured.out
    assert "blocks" in captured.out
    assert "dots" in captured.out
    assert "arrows" in captured.out
    assert "squares" in captured.out
    assert "lines" in captured.out
    assert "Animated Progress:" in captured.out
    assert "Loading" in captured.out
    assert "Segmented Progress Bar:" in captured.out
    assert "Tutorial Progress" in captured.out
    assert "Spinners:" in captured.out
    assert "Custom Colors:" in captured.out