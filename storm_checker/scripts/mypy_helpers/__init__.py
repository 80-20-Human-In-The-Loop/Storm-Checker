"""
MyPy Helper Modules for Storm-Checker
=====================================
Modular components for type checking functionality.
"""

from .display_helpers import (
    print_storm_header,
    print_results_standard,
    print_results_educational,
    print_next_steps_standard,
    print_next_steps_educational,
    print_dashboard,
)

from .analysis_helpers import (
    suggest_tutorials,
    print_learning_path,
    show_random_issue,
)

from .utility_helpers import (
    check_pyproject_config,
    filter_and_categorize_errors,
    setup_tracking_session,
    process_json_output,
    get_file_errors,
)

__all__ = [
    # Display helpers
    'print_storm_header',
    'print_results_standard',
    'print_results_educational',
    'print_next_steps_standard',
    'print_next_steps_educational',
    'print_dashboard',
    # Analysis helpers
    'suggest_tutorials',
    'print_learning_path',
    'show_random_issue',
    # Utility helpers
    'check_pyproject_config',
    'filter_and_categorize_errors',
    'setup_tracking_session',
    'process_json_output',
    'get_file_errors',
]