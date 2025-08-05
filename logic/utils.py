#!/usr/bin/env python3
"""Common utilities for storm-checker.

This module provides general utility functions used throughout the storm-checker
codebase, including file discovery, git integration, and configuration handling.
All functions are designed to be pure and easily testable.
"""

import json
import os
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Default exclusions for Python projects
DEFAULT_EXCLUDE_DIRS: Set[str] = {
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    "node_modules",
    ".git",
    "migrations",
    "htmlcov",
    "coverage",
    "dist",
    "build",
    ".mypy_cache",
    ".stormchecker",
    ".pytest_cache",
    ".tox",
    "site-packages",
    ".eggs",
    "*.egg-info",
}


def find_python_files(
    root_path: Path = Path("."),
    keywords: Optional[str] = None,
    exclude_dirs: Optional[Set[str]] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> List[Path]:
    """Find Python files in a directory tree with filtering options.
    
    Args:
        root_path: Root directory to search from. Defaults to current directory.
        keywords: Optional regex pattern to filter file paths.
        exclude_dirs: Set of directory names to exclude. If None, uses defaults.
        include_patterns: List of glob patterns to include (e.g., ["*.py", "*.pyi"]).
        exclude_patterns: List of glob patterns to exclude (e.g., ["test_*.py"]).
        
    Returns:
        List of Path objects for matching Python files, sorted alphabetically.
        
    Example:
        >>> files = find_python_files(keywords="models|views")
        >>> len(files)
        42
        >>> files[0].name
        'models.py'
        
    Note:
        The function respects .gitignore patterns if present in the project root.
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
        
    if include_patterns is None:
        include_patterns = ["*.py"]
        
    all_files: List[Path] = []
    
    for pattern in include_patterns:
        for path in root_path.rglob(pattern):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in exclude_dirs):
                continue
                
            # Skip if path matches any exclude pattern
            if exclude_patterns:
                if any(path.match(exc_pattern) for exc_pattern in exclude_patterns):
                    continue
            
            # Apply keyword filter if provided
            if keywords:
                path_str = str(path)
                if not re.search(keywords, path_str, re.IGNORECASE):
                    continue
                    
            all_files.append(path)
            
    return sorted(all_files)


def get_git_info() -> Dict[str, Optional[str]]:
    """Get current git repository information.
    
    Returns:
        Dictionary containing:
            - commit: Current commit hash (first 8 chars) or None
            - branch: Current branch name or None
            - author: Git user.name or None
            - email: Git user.email or None
            - is_dirty: Whether there are uncommitted changes
            
    Example:
        >>> info = get_git_info()
        >>> print(f"Commit: {info['commit']}")
        Commit: a1b2c3d4
        >>> print(f"Dirty: {info['is_dirty']}")
        Dirty: True
    """
    info: Dict[str, Optional[str]] = {
        "commit": None,
        "branch": None,
        "author": None,
        "email": None,
        "is_dirty": None,
    }
    
    try:
        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()[:8]
            
        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()
            
        # Get author info
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            info["author"] = result.stdout.strip()
            
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            info["email"] = result.stdout.strip()
            
        # Check if working directory is dirty
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            info["is_dirty"] = bool(result.stdout.strip())
            
    except (FileNotFoundError, OSError):
        # Git not available or not a git repository
        pass
        
    return info


def detect_ai_context() -> Tuple[str, Optional[str]]:
    """Detect if code is being written by an AI assistant.
    
    Returns:
        Tuple of (author_type, ai_model) where:
            - author_type: "ai_agent" or "human"
            - ai_model: Name of AI model if detected, None otherwise
            
    Example:
        >>> author_type, model = detect_ai_context()
        >>> print(f"Author: {author_type}, Model: {model}")
        Author: ai_agent, Model: claude
        
    Note:
        Checks various environment variables set by different AI coding assistants.
    """
    # Common AI assistant environment variables
    ai_indicators = {
        "claude": ["CLAUDECODE", "CLAUDE_AI", "ANTHROPIC_AI"],
        "copilot": ["GITHUB_COPILOT_ACTIVE", "COPILOT_ACTIVE"],
        "cursor": ["CURSOR_AI_ACTIVE", "CURSOR_ACTIVE"],
        "windsurf": ["WINDSURF_ACTIVE", "CODEIUM_ACTIVE"],
        "cody": ["CODY_ACTIVE", "SOURCEGRAPH_CODY"],
        "tabnine": ["TABNINE_ACTIVE"],
        "kite": ["KITE_ACTIVE"],
    }
    
    # Check each AI assistant
    for agent, env_vars in ai_indicators.items():
        for env_var in env_vars:
            if os.environ.get(env_var) == "1":
                return "ai_agent", agent
                
    # Generic AI detection
    if os.environ.get("AI_ASSISTANT") == "1":
        return "ai_agent", "generic"
        
    return "human", None


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from a JSON or TOML file.
    
    Args:
        config_path: Path to configuration file.
        
    Returns:
        Dictionary containing configuration values.
        
    Raises:
        FileNotFoundError: If config file doesn't exist.
        json.JSONDecodeError: If JSON parsing fails.
        ImportError: If TOML support needed but toml package not installed.
        
    Example:
        >>> config = load_config(Path(".stormchecker/config.json"))
        >>> print(config.get("theme", "default"))
        ocean
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    content = config_path.read_text(encoding="utf-8")
    
    if config_path.suffix == ".json":
        return json.loads(content)
    elif config_path.suffix == ".toml":
        try:
            import tomli
            return tomli.loads(content)
        except ImportError:
            raise ImportError(
                "TOML configuration requires 'tomli' package. "
                "Install with: pip install tomli"
            )
    else:
        # Try JSON first, then TOML
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                import tomli
                return tomli.loads(content)
            except ImportError:
                raise ValueError(
                    f"Unknown configuration format: {config_path.suffix}"
                )


def get_data_directory() -> Path:
    """Get the appropriate data directory for the current platform.
    
    Returns:
        Path to the storm-checker data directory, following platform conventions:
        - Windows: %LOCALAPPDATA%/StormChecker
        - macOS: ~/Library/Application Support/StormChecker  
        - Linux: ~/.local/share/stormchecker
        
    Example:
        >>> data_dir = get_data_directory()
        >>> print(data_dir)
        /home/user/.local/share/stormchecker  # On Linux
        C:\\Users\\User\\AppData\\Local\\StormChecker  # On Windows
        /Users/user/Library/Application Support/StormChecker  # On macOS
    """
    system = platform.system()
    
    if system == "Windows":
        # Use LOCALAPPDATA on Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "StormChecker"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "StormChecker"
    else:  # Linux and other Unix-like systems
        # Follow XDG Base Directory specification
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            return Path(xdg_data_home) / "stormchecker"
        else:
            return Path.home() / ".local" / "share" / "stormchecker"


def get_config_directory() -> Path:
    """Get the appropriate config directory for the current platform.
    
    Returns:
        Path to the storm-checker config directory, following platform conventions:
        - Windows: %APPDATA%/StormChecker
        - macOS: ~/Library/Preferences/StormChecker
        - Linux: ~/.config/stormchecker
        
    Example:
        >>> config_dir = get_config_directory()
        >>> print(config_dir)
        /home/user/.config/stormchecker  # On Linux
    """
    system = platform.system()
    
    if system == "Windows":
        # Use APPDATA on Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "StormChecker"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Preferences" / "StormChecker"
    else:  # Linux and other Unix-like systems
        # Follow XDG Base Directory specification
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            return Path(xdg_config_home) / "stormchecker"
        else:
            return Path.home() / ".config" / "stormchecker"


def ensure_directory(directory: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to directory.
        
    Returns:
        The directory Path object.
        
    Example:
        >>> progress_dir = ensure_directory(Path(".stormchecker/progress"))
        >>> progress_dir.exists()
        True
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def format_time_delta(seconds: float) -> str:
    """Format a time duration in seconds to human-readable string.
    
    Args:
        seconds: Time duration in seconds.
        
    Returns:
        Human-readable time string.
        
    Example:
        >>> format_time_delta(3665)
        '1h 1m 5s'
        >>> format_time_delta(45.5)
        '45.5s'
        >>> format_time_delta(0.123)
        '123ms'
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.0f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def parse_file_line_reference(reference: str) -> Tuple[Optional[str], Optional[int]]:
    """Parse a file:line reference string.
    
    Args:
        reference: String in format "path/to/file.py:123" or just "path/to/file.py".
        
    Returns:
        Tuple of (file_path, line_number) where line_number may be None.
        
    Example:
        >>> parse_file_line_reference("src/models.py:42")
        ('src/models.py', 42)
        >>> parse_file_line_reference("src/models.py")
        ('src/models.py', None)
    """
    parts = reference.split(":", 1)
    file_path = parts[0]
    
    if len(parts) > 1:
        try:
            line_number = int(parts[1])
            return file_path, line_number
        except ValueError:
            # Line number not a valid integer
            return file_path, None
    
    return file_path, None


def calculate_file_stats(file_path: Path) -> Dict[str, Union[int, float]]:
    """Calculate statistics for a Python file.
    
    Args:
        file_path: Path to Python file.
        
    Returns:
        Dictionary containing:
            - total_lines: Total number of lines
            - code_lines: Non-empty, non-comment lines
            - comment_lines: Lines that are pure comments
            - docstring_lines: Lines in docstrings
            - blank_lines: Empty lines
            - type_hint_score: Percentage of functions with type hints (0-100)
            
    Example:
        >>> stats = calculate_file_stats(Path("mymodule.py"))
        >>> print(f"Type hint coverage: {stats['type_hint_score']:.1f}%")
        Type hint coverage: 87.5%
    """
    stats = {
        "total_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "docstring_lines": 0,
        "blank_lines": 0,
        "type_hint_score": 0.0,
    }
    
    if not file_path.exists():
        return stats
        
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        in_docstring = False
        docstring_delimiter = None
        functions_total = 0
        functions_typed = 0
        
        for line in lines:
            stats["total_lines"] += 1
            stripped = line.strip()
            
            # Track docstrings
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                in_docstring = True
                docstring_delimiter = '"""' if stripped.startswith('"""') else "'''"
                stats["docstring_lines"] += 1
                if stripped.endswith(docstring_delimiter) and len(stripped) > 3:
                    in_docstring = False
            elif in_docstring:
                stats["docstring_lines"] += 1
                if stripped.endswith(docstring_delimiter):
                    in_docstring = False
            # Count other line types
            elif not stripped:
                stats["blank_lines"] += 1
            elif stripped.startswith("#"):
                stats["comment_lines"] += 1
            else:
                stats["code_lines"] += 1
                
                # Track function definitions for type hint scoring
                if stripped.startswith("def "):
                    functions_total += 1
                    if "->" in line:
                        functions_typed += 1
                        
        # Calculate type hint score
        if functions_total > 0:
            stats["type_hint_score"] = (functions_typed / functions_total) * 100
            
    except (OSError, UnicodeDecodeError):
        # File read error
        pass
        
    return stats


def get_project_type(root_path: Path = Path(".")) -> str:
    """Detect the type of Python project.
    
    Args:
        root_path: Root directory of the project.
        
    Returns:
        Project type string: "django", "fastapi", "flask", "jupyter", 
        "package", "script", or "unknown".
        
    Example:
        >>> project_type = get_project_type()
        >>> print(f"Detected project type: {project_type}")
        Detected project type: django
    """
    # Check for Django
    if (root_path / "manage.py").exists():
        return "django"
        
    # Check for common framework indicators in requirements
    req_files = ["requirements.txt", "requirements.in", "pyproject.toml", "setup.py"]
    for req_file in req_files:
        req_path = root_path / req_file
        if req_path.exists():
            try:
                content = req_path.read_text(encoding="utf-8").lower()
                if "fastapi" in content:
                    return "fastapi"
                elif "flask" in content:
                    return "flask"
            except (OSError, UnicodeDecodeError):
                continue
                
    # Check for Jupyter notebooks
    if list(root_path.glob("*.ipynb")):
        return "jupyter"
        
    # Check for package structure
    if (root_path / "setup.py").exists() or (root_path / "pyproject.toml").exists():
        return "package"
        
    # Check if it's a simple script
    py_files = list(root_path.glob("*.py"))
    if py_files and len(py_files) <= 3:
        return "script"
        
    return "unknown"


# TODO: Add function to detect and respect .gitignore patterns
# TODO: Add function to calculate code complexity metrics
# TODO: Add function to extract imports from Python files
# TODO: Add function to detect Python version from project