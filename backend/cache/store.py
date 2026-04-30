"""Dictionary cache using JSON file storage.

Caches dictionary lookup results by lemma to reduce API calls.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from config_paths import get_cache_file

CACHE_FILE = get_cache_file()
MAX_CACHE_SIZE = 10000  # Max entries


class DictCache:
    """Simple JSON-based dictionary cache."""

    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self._data: dict[str, Any] = {}
        self._load()

    def get(self, lemma: str) -> Optional[dict]:
        """Get cached result for a lemma."""
        entry = self._data.get(lemma)
        if entry:
            # Update last_used_at
            entry["last_used_at"] = time.time()
            return entry
        return None

    def set(self, lemma: str, data: dict):
        """Cache a dictionary lookup result."""
        if lemma not in self._data:
            # Enforce max cache size
            if len(self._data) >= MAX_CACHE_SIZE:
                self._evict()

        self._data[lemma] = {
            **data,
            "lemma": lemma,
            "created_at": data.get("created_at", time.time()),
            "last_used_at": time.time(),
        }
        self._save()

    def _load(self):
        """Load cache from disk."""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._data = {}

    def _save(self):
        """Save cache to disk."""
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass  # Silent fail - cache is optional

    def _evict(self):
        """Evict oldest entries to make room."""
        if not self._data:
            return

        # Sort by last_used_at, remove oldest 20%
        entries = sorted(
            self._data.items(),
            key=lambda x: x[1].get("last_used_at", 0),
        )
        evict_count = max(1, len(entries) // 5)
        for key, _ in entries[:evict_count]:
            del self._data[key]


def create_cache():
    """Create a dictionary cache instance."""
    return DictCache(str(CACHE_FILE))
