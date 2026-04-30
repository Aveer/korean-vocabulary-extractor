"""Dictionary provider abstraction and implementations.

Provides Korean-English dictionary lookups with caching.
Works in degraded mode without API key.
"""

from abc import ABC, abstractmethod
from typing import Optional


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


def create_provider() -> DictionaryProvider:
    """Create the appropriate dictionary provider based on config.

    Returns NIKL provider if API key is available, otherwise
    returns a null provider that works in degraded mode.
    """
    import os
    from dictionary.nikl import NIKLProvider

    api_key = os.environ.get("KRDICT_API_KEY", "").strip()
    if api_key:
        return NIKLProvider(api_key)
    return NullProvider()


class NullProvider(DictionaryProvider):
    """Null provider for degraded mode (no API key)."""

    def lookup(self, lemma: str) -> tuple[list[str], Optional[str], Optional[str]]:
        return [], None, None

    def is_available(self) -> bool:
        return False
