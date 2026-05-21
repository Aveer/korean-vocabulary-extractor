"""NIKL (National Institute of Korean Language) dictionary provider.

Uses the Korean-English Learners' Dictionary API:
https://www.korean.go.kr/portal/outer/main.do

API endpoint:
https://api.korean.go.kr/openApi/wordServlet.en
"""

import logging
import os
import time
from typing import Optional

import httpx

from dictionary.provider import DictionaryProvider
from cache.store import create_cache


logger = logging.getLogger(__name__)


class NIKLProvider(DictionaryProvider):
    """NIKL Korean-English Learners' Dictionary API provider."""

    BASE_URL = "https://api.korean.go.kr/openApi/wordServlet.en"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(timeout=10.0)
        self.cache = create_cache()
        self._last_request_time = 0
        self._min_request_interval = 0.5  # Rate limit: 2 requests/sec

    def lookup(self, lemma: str) -> tuple[list[str], Optional[str], Optional[str]]:
        """Look up a lemma in the NIKL dictionary.

        Returns:
            Tuple of (english_glosses, korean_definition, topik_level).
        """
        # Check cache first
        cached = self.cache.get(lemma)
        if cached:
            return (
                cached.get("glosses", []),
                cached.get("definition"),
                cached.get("level"),
            )

        # API request with rate limiting
        self._rate_limit()

        try:
            response = self._make_request(lemma)
            result = self._parse_response(response, lemma)

            # Cache the result
            self.cache.set(lemma, {
                "glosses": result[0],
                "definition": result[1],
                "level": result[2],
                "provider": "NIKL",
                "created_at": time.time(),
            })

            return result
        except Exception as exc:
            logger.warning(
                "NIKL dictionary lookup failed for lemma=%s (error=%s)",
                lemma,
                type(exc).__name__,
            )
            # Degraded mode: return empty results
            return [], None, None

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _rate_limit(self):
        """Enforce rate limiting for API requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, lemma: str) -> dict:
        """Make API request to NIKL dictionary."""
        params = {
            "key": self.api_key,
            "search": lemma,
            "type": "json",
        }
        response = self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()

    def _parse_response(self, data: dict, lemma: str) -> tuple[list[str], Optional[str], Optional[str]]:
        """Parse NIKL API response.

        The API returns a complex nested structure. We extract:
        - English glosses/translations
        - Korean definitions
        - TOPIK level if available
        """
        glosses = []
        definition = None
        level = None

        try:
            # NIKL API response structure varies; handle common patterns
            channel = data.get("channel", {})
            items = channel.get("item", [])

            for item in items:
                # Extract English translations
                trans = item.get("trans", [])
                if isinstance(trans, list):
                    for t in trans:
                        if isinstance(t, dict):
                            en = t.get("en", [])
                            if isinstance(en, list):
                                glosses.extend([e for e in en if e])
                            elif en:
                                glosses.append(en)
                        elif t:
                            glosses.append(str(t))

                # Extract Korean definitions
                kr = item.get("kr", [])
                if isinstance(kr, list) and kr:
                    definition = " ".join(str(k) for k in kr if k)
                elif kr:
                    definition = str(kr)

                # Extract TOPIK level
                topik = item.get("topik", {})
                if topik:
                    level_str = topik.get("level", topik.get("grade", ""))
                    if level_str:
                        level = self._map_topik_level(str(level_str))

        except (KeyError, TypeError, IndexError):
            pass

        # Deduplicate glosses
        seen = set()
        unique_glosses = []
        for g in glosses:
            g_lower = g.lower().strip()
            if g_lower and g_lower not in seen:
                seen.add(g_lower)
                unique_glosses.append(g.strip())

        return unique_glosses, definition, level

    def _map_topik_level(self, level_str: str) -> Optional[str]:
        """Map NIKL level string to our TOPIK level format."""
        level_str = level_str.strip()
        level_map = {
            "1": "TOPIK_I_1",
            "2": "TOPIK_I_2",
            "3": "TOPIK_II_3",
            "4": "TOPIK_II_4",
            "5": "TOPIK_II_5",
            "6": "TOPIK_II_6",
        }
        return level_map.get(level_str)
