import pytest
from storm_checker.cli.components.progress_dashboard import ProgressDashboard

def test_progress_dashboard_initialization():
    """Test that the ProgressDashboard can be initialized."""
    try:
        dashboard = ProgressDashboard()
        assert isinstance(dashboard, ProgressDashboard)
    except Exception as e:
        pytest.fail(f"ProgressDashboard initialization failed with an exception: {e}")
