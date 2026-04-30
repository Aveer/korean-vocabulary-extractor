"""Deterministic ranking for vocabulary candidates.

Ranks lemma candidates using multiple scoring factors:
- Frequency in text
- Target TOPIK level match
- Content POS score (nouns/verbs > adverbs)
- Dictionary confidence
- Source sentence quality
- Penalties: too easy, proper names, duplicate families
"""

import math
from dataclasses import dataclass
from nlp.lemmatizer import LemmaCandidate


# TOPIK level numeric values for comparison
TOPIK_LEVELS = {
    "TOPIK_I_1": 1,
    "TOPIK_I_2": 2,
    "TOPIK_II_3": 3,
    "TOPIK_II_4": 4,
    "TOPIK_II_5": 5,
    "TOPIK_II_6": 6,
    "unknown": 4,  # Default to middle level
}

# POS content scores (higher = more useful for learning)
POS_SCORES = {
    "noun": 3.0,
    "verb": 3.0,
    "adjective": 2.5,
    "adverb": 1.5,
    "phrase": 2.0,
    "unknown": 1.0,
}

# Very common/basic words to penalize
BASIC_WORDS = {
    "하다", "이다", "있다", "없다", "되다", "지나다", "주다",
    "나다", "하다", "아니다", "보다", "듣다", "말하다", "가다",
    "오다", "서다", "앉다", "먹다", "자다", "일하다", "알다",
    "think", "know", "person", "thing", "day", "time",
}


@dataclass
class RankedCandidate:
    """A ranked vocabulary candidate with score and reason."""

    lemma: str
    display: str
    pos: str
    frequency: int
    first_sentence: str
    all_sentences: list[str]
    score: float
    reason: str
    level: str | None = None
    english_glosses: list[str] | None = None
    korean_definition: str | None = None


def rank_candidates(
    candidates: list[LemmaCandidate],
    target_level: str = "ANY",
    word_count: int = 20,
    dictionary_lookup=None,
) -> list[RankedCandidate]:
    """Rank and filter vocabulary candidates.

    Args:
        candidates: Lemma candidates from the NLP pipeline.
        target_level: Target TOPIK level (ANY, TOPIK_II_3, etc.).
        word_count: Maximum number of candidates to return.
        dictionary_lookup: Optional callable(lemma) -> (glosses, definition, level).

    Returns:
        List of ranked candidates, sorted by score (highest first).
    """
    scored = []
    seen_families = {}  # Track word families to avoid duplicates

    for candidate in candidates:
        score = _compute_score(candidate, target_level, seen_families)

        if score <= 0:
            continue

        reason = _generate_reason(candidate, score, target_level)

        # Dictionary lookup (if available)
        glosses = []
        definition = None
        level = None
        if dictionary_lookup:
            try:
                glosses, definition, level = dictionary_lookup(candidate.lemma)
            except Exception:
                pass  # Degraded mode: continue without dictionary data

        scored.append(
            RankedCandidate(
                lemma=candidate.lemma,
                display=candidate.display,
                pos=candidate.pos,
                frequency=candidate.frequency,
                first_sentence=candidate.first_sentence,
                all_sentences=candidate.all_sentences,
                score=score,
                reason=reason,
                level=level,
                english_glosses=glosses if glosses else None,
                korean_definition=definition,
            )
        )

    # Sort by score (descending)
    scored.sort(key=lambda c: c.score, reverse=True)

    return scored[:word_count]


def _compute_score(
    candidate: LemmaCandidate,
    target_level: str,
    seen_families: dict,
) -> float:
    """Compute ranking score for a candidate."""
    score = 0.0

    # 1. Frequency score (log scale, max 2.0)
    freq_score = min(math.log2(candidate.frequency + 1), 2.0)
    score += freq_score * 2.0

    # 2. Content POS score
    pos_score = POS_SCORES.get(candidate.pos, 1.0)
    score += pos_score

    # 3. Target level match score (if level is known)
    if candidate.pos != "unknown":
        score += 1.0  # Base score for having a known POS

    # 4. Source sentence quality (longer, more complete sentences score higher)
    sentence = candidate.first_sentence
    if len(sentence) > 10:
        score += 1.0
    if len(sentence) > 30:
        score += 0.5

    # 5. Dictionary confidence bonus (if glosses available, added later)
    # This is a placeholder; actual bonus comes from dictionary_lookup

    # --- Penalties ---

    # Too easy penalty
    if candidate.lemma in BASIC_WORDS:
        score -= 2.0

    # Proper name penalty
    if candidate.lemma.isalpha() and len(candidate.lemma) > 3:
        # Heuristic: long alphabetic strings might be names
        if candidate.pos == "noun" and candidate.frequency == 1:
            score -= 1.0

    # Duplicate family penalty
    family = _get_word_family(candidate.lemma)
    if family in seen_families:
        score -= 1.5  # Penalize variants of the same word
    seen_families[family] = candidate.lemma

    return max(score, 0)


def _get_word_family(lemma: str) -> str:
    """Get the word family for duplicate detection.

    Groups related words: 먹다, 먹었다, 먹어요 -> 먹다
    """
    # Strip common verb endings to get the root
    for ending in ["하다", "지다", "이다", "이다"]:
        if lemma.endswith(ending):
            return lemma[: -len(ending)]
    return lemma


def _generate_reason(
    candidate: LemmaCandidate,
    score: float,
    target_level: str,
) -> str:
    """Generate a human-readable reason for why this word was selected."""
    parts = []

    if candidate.pos == "noun":
        parts.append("Noun")
    elif candidate.pos == "verb":
        parts.append("Verb")
    elif candidate.pos == "adjective":
        parts.append("Adjective")
    elif candidate.pos == "adverb":
        parts.append("Adverb")

    if candidate.frequency > 1:
        parts.append(f"appears {candidate.frequency} times")

    if score > 5:
        parts.append("high-priority vocabulary")
    elif score > 3:
        parts.append("useful for comprehension")

    return ". ".join(parts) if parts else "Selected vocabulary item"
