import pytest
from storm_checker.cli.components.tutorial_renderer import TutorialRenderer

def test_tutorial_renderer_initialization():
    """Test that the TutorialRenderer can be initialized."""
    try:
        renderer = TutorialRenderer()
        assert isinstance(renderer, TutorialRenderer)
    except Exception as e:
        pytest.fail(f"TutorialRenderer initialization failed with an exception: {e}")
