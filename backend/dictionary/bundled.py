"""Bundled offline dictionary provider using kengdic dataset.

Provides Korean-English dictionary lookups from a bundled JSON file.
No API key required. Works offline.

Source: kengdic (Joe Speigle's Korean/English Dictionary)
License: MPL 2.0 / LGPL 2.0+
URL: https://github.com/garfieldnate/kengdic
"""

import json
import sys
from pathlib import Path
from typing import Optional

from dictionary.provider import DictionaryProvider

def _candidate_paths() -> list[Path]:
    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "bundled_dict.json",
        base_dir.parent / "backend" / "dictionary" / "bundled_dict.json",
        base_dir.parent / "dictionary" / "bundled_dict.json",
    ]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        frozen_root = Path(meipass)
        candidates.extend([
            frozen_root / "backend" / "dictionary" / "bundled_dict.json",
            frozen_root / "dictionary" / "bundled_dict.json",
        ])
    return candidates


class BundledProvider(DictionaryProvider):
    """Offline dictionary provider using bundled kengdic dataset."""

    def __init__(self):
        self._entries: dict[str, dict] = {}
        self._source: str = ""
        self._load()

    def _load(self):
        """Load bundled dictionary from JSON file."""
        try:
            dict_path = next((p for p in _candidate_paths() if p.exists()), None)
            if not dict_path:
                raise OSError("bundled_dict.json not found")
            with open(dict_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = data.get("entries", {})
            self._source = data.get("source", "kengdic")
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load bundled dictionary: {e}")
            self._entries = {}

    def lookup(self, lemma: str) -> tuple[list[str], Optional[str], Optional[str]]:
        """Look up a lemma in the bundled dictionary.

        Returns:
            Tuple of (english_glosses, korean_definition, topik_level).
            korean_definition and topik_level are always None for bundled dict.
        """
        entry = self._entries.get(lemma)
        if not entry:
            return [], None, None
        glosses = entry.get("glosses", [])
        return glosses, None, None

    def is_available(self) -> bool:
        return bool(self._entries)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def source(self) -> str:
        return self._source
