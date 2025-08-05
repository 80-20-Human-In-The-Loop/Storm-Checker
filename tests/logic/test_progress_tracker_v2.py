import pytest
from storm_checker.logic.progress_tracker_v2 import EnhancedProgressTracker

def test_enhanced_progress_tracker_initialization():
    """Test that the EnhancedProgressTracker can be initialized."""
    try:
        tracker = EnhancedProgressTracker()
        assert isinstance(tracker, EnhancedProgressTracker)
    except Exception as e:
        pytest.fail(f"EnhancedProgressTracker initialization failed with an exception: {e}")
