"""Dictionary provider abstraction, implementations, and config management.

Provides Korean-English dictionary lookups with caching.
Supports bundled offline dictionary and NIKL API.
Config stored in JSON file for persistence across requests.
"""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from config_paths import get_config_path

# Config file for dictionary settings — uses APPDATA on Windows, project-relative in dev
CONFIG_PATH = get_config_path()
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


def _load_env_files() -> None:
    backend_env = BACKEND_DIR / ".env"
    load_dotenv(backend_env, override=False)
    root_env = ROOT_DIR / ".env"
    if root_env != backend_env and root_env.exists():
        load_dotenv(root_env, override=False)


_load_env_files()


class DictionaryProvider(ABC):
    """Abstract dictionary provider interface."""

    @abstractmethod
    def lookup(self, lemma: str) -> tuple[list[str], Optional[str], Optional[str]]:
        """Look up a lemma in the dictionary.

        Returns:
            Tuple of (english_glosses, korean_definition, topik_level).
            Returns empty lists/None if not found.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the dictionary provider is available."""
        ...


def get_config() -> dict:
    """Load dictionary config from file."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {
        "provider": "bundled",
        "api_key": os.environ.get("KRDICT_API_KEY", "").strip() or "",
    }


def save_config(config: dict):
    """Save dictionary config to file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def create_provider(provider_name: str | None = None) -> DictionaryProvider:
    """Create the appropriate dictionary provider based on config.

    Args:
        provider_name: Override provider name ('bundled', 'nikl', or None for auto).

    Returns:
        Dictionary provider instance.
    """
    from dictionary.bundled import BundledProvider
    from dictionary.nikl import NIKLProvider

    if provider_name:
        chosen = provider_name
        api_key = ""
    else:
        config = get_config()
        chosen = config.get("provider", "bundled")
        api_key = config.get("api_key", "").strip() or os.environ.get("KRDICT_API_KEY", "").strip()

    if chosen == "nikl" and api_key:
        return NIKLProvider(api_key)
    # Default to bundled (always available)
    return BundledProvider()
