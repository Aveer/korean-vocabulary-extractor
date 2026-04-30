"""Google Translate sentence translator with caching."""

from deep_translator import GoogleTranslator
import hashlib


class SentenceTranslator:
    """Translate Korean sentences to English using Google Translate.

    Uses an in-memory cache to avoid redundant API calls for repeated sentences.
    """

    def __init__(self, cache_size: int = 500):
        self._translator = GoogleTranslator(source="ko", target="en")
        self._cache: dict[str, str] = {}
        self._cache_size = cache_size

    def translate(self, sentence: str) -> str | None:
        """Translate a Korean sentence to English.

        Returns None on failure (network error, empty input, etc.)
        """
        if not sentence or not sentence.strip():
            return None

        # Check cache
        cache_key = sentence.strip()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = self._translator.translate(cache_key)
            if result:
                # Evict oldest entry if cache is full
                if len(self._cache) >= self._cache_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                self._cache[cache_key] = result
            return result
        except Exception:
            # Fail gracefully - return None so study line still works without translation
            return None
