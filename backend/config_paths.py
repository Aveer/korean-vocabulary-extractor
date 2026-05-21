"""Shared path utilities for user data directories.

Uses %APPDATA% on Windows, XDG_DATA_HOME on Linux, ~/Library/Application Support on macOS.
Fallback: project-relative cache_data/ directory for development.
"""

import os
import sys
from pathlib import Path

APP_NAME = "KoreanVocabExtractor"


def _get_app_data_dir() -> Path:
    """Get the application data directory for the current platform."""
    override = os.environ.get("KVE_DATA_DIR")
    if override:
        return Path(override)

    # Windows: %APPDATA%/KoreanVocabExtractor/
    if os.name == "nt" or "APPDATA" in os.environ:
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / APP_NAME

    # macOS: ~/Library/Application Support/KoreanVocabExtractor/
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    # Linux/Unix: $XDG_DATA_HOME/KoreanVocabExtractor/
    if os.environ.get("XDG_DATA_HOME"):
        return Path(os.environ["XDG_DATA_HOME"]) / APP_NAME

    # Linux fallback: ~/.local/share/KoreanVocabExtractor/
    home = Path.home()
    xdg_data = home / ".local" / "share" / APP_NAME
    if home.exists():
        return xdg_data

    # Last resort: return None so callers fall back to project-relative paths
    return Path("")


def get_data_dir() -> Path:
    """Get the data directory for config and cache files.

    Returns a user-writable directory for storing dictionary config,
    cache data, and other persistent settings.

    Returns:
        Path to the application data directory, or empty Path if unavailable.
    """
    return _get_app_data_dir()


def get_config_path() -> Path:
    """Get the path to the dictionary configuration file."""
    data_dir = get_data_dir()
    if data_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "dictionary_config.json"
    # Fallback: project-relative path (for development)
    return Path(__file__).parent.parent / "cache_data" / "dictionary_config.json"


def get_cache_dir() -> Path:
    """Get the directory for dictionary cache files."""
    data_dir = get_data_dir()
    if data_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    # Fallback: project-relative path (for development)
    return Path(__file__).parent.parent / "cache_data"


def get_cache_file() -> Path:
    """Get the path to the dictionary cache file."""
    return get_cache_dir() / "dictionary_cache.json"
