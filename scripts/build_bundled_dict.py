"""Download kengdic TSV and convert to a compact bundled dictionary JSON.

Output: backend/dictionary/bundled_dict.json
License: MPL 2.0 / LGPL 2.0+ (Joe Speigle's Kengdic)
Source: https://github.com/garfieldnate/kengdic
"""

import csv
import json
import re
import sys
from pathlib import Path

import httpx

KENGDIC_URL = "https://raw.githubusercontent.com/garfieldnate/kengdic/master/kengdic.tsv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "backend" / "dictionary" / "bundled_dict.json"

# TSV columns: id, surface, hanja, gloss, level, created, source
# We only need: surface (Korean word), gloss (English), level (TOPIK level if any)

# Korean syllable range (most common Korean characters)
KOREAN_SYLLABLE_PATTERN = re.compile(r"^[\uac00-\ud7af]+$")
# Korean jamo (individual letters) - skip these
KOREAN_JAMO_PATTERN = re.compile(r"^[\u1100-\u11ff\u3130-\u318f]+$")


def is_korean_word(word: str) -> bool:
    """Check if a string is a valid Korean word (syllables only, no jamo)."""
    # Must be pure Korean syllables
    if not KOREAN_SYLLABLE_PATTERN.match(word):
        return False
    # Skip jamo (individual letters)
    if KOREAN_JAMO_PATTERN.match(word):
        return False
    return True


def clean_gloss(gloss: str | None) -> list[str]:
    """Parse and clean English gloss into a list of translations."""
    if not gloss or not gloss.strip():
        return []
    # Split on semicolons for multiple meanings
    parts = re.split(r"[;]", gloss.strip())
    cleaned = []
    for p in parts:
        p = p.strip().strip('"').strip()
        if p and len(p) > 1:
            cleaned.append(p)
    return cleaned[:5]  # Keep top 5 translations


# kengdic level is A/B/C/D (internal classification, not TOPIK)
# We don't map it to TOPIK levels


def main():
    print(f"Downloading kengdic from {KENGDIC_URL}...")
    response = httpx.get(KENGDIC_URL, timeout=120)
    response.raise_for_status()

    print("Parsing TSV...")
    reader = csv.reader(response.text.splitlines(), delimiter="\t")
    next(reader, None)  # Skip header

    entries = {}
    skipped = 0
    kept = 0

    for row in reader:
        if len(row) < 4:
            continue

        surface = row[1].strip()
        gloss_raw = row[3].strip() if len(row) > 3 and row[3] else ""

        # Skip entries with spaces (phrases/sentences)
        if " " in surface:
            skipped += 1
            continue

        # Skip very short entries (1 char)
        if len(surface) < 2:
            skipped += 1
            continue

        # Skip very long entries (likely phrases/sentences)
        if len(surface) > 12:
            skipped += 1
            continue

        # Skip non-Korean entries
        if not is_korean_word(surface):
            skipped += 1
            continue

        # Skip entries with no English gloss
        glosses = clean_gloss(gloss_raw)
        if not glosses:
            skipped += 1
            continue

        # Skip entries where gloss looks like a Korean phrase (no real English)
        if all(any(c in g for c in "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ") for g in glosses):
            skipped += 1
            continue

        # Skip grammar/morphology entries (contain + in gloss)
        if "+" in gloss_raw:
            skipped += 1
            continue

        entries[surface] = {
            "glosses": glosses,
        }
        kept += 1

    # Build final dict
    output = {
        "source": "kengdic (Joe Speigle's Korean/English Dictionary)",
        "license": "MPL 2.0 / LGPL 2.0+",
        "url": "https://github.com/garfieldnate/kengdic",
        "total_entries": len(entries),
        "entries": dict(sorted(entries.items())),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Done! {kept} entries kept, {skipped} skipped.")
    print(f"Output: {OUTPUT_PATH}")
    print(f"File size: {OUTPUT_PATH.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
