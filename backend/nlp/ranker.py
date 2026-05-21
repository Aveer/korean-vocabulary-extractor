"""Deterministic ranking for vocabulary candidates.

Ranks lemma candidates using multiple scoring factors:
- Level fit score (major factor)
- Difficulty score
- Dictionary confidence
- Content POS score
- Frequency score (reduced weight)
- Source fragment quality
- Penalties: too easy, proper names, duplicate families
"""

import logging
import math
from dataclasses import dataclass, field
from nlp.lemmatizer import LemmaCandidate


logger = logging.getLogger(__name__)


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

# Ultra-basic words to strongly penalize at higher levels
BASIC_WORDS = {
    # Core verbs
    "하다", "이다", "있다", "없다", "되다", "지나다", "주다",
    "나다", "아니다", "보다", "듣다", "말하다", "가다",
    "오다", "서다", "앉다", "먹다", "자다", "일하다", "알다",
    # Basic nouns/adjectives
    "사람", "남자", "여자", "집", "일", "돈", "좋다", "크다", "작다",
    "것", "때", "곳", "년", "달", "시간", "분", "나라", "세계",
    # Basic adverbs (very common, TOPIK I level)
    "지금", "다시", "이렇게", "그렇게", "잘", "못", "순간", "그래도",
    "그래서", "또", "또한", "모두", "매우", "여기", "저기", "거기",
    "이제", "벌써", "아직", "이미", "먼저", "나중", "끝", "처음",
    "또는", "혹은", "아니면", "그리고", "하지만", "그러나", "그런데",
    "아니", "네", "예", "아니요",
    "이곳", "저곳", "그곳", "저렇게",
    "누구", "무엇", "어디", "언제", "왜", "어떻게",
    "각각", "모든", "일부", "어떤", "아무",
    "없음", "없어",
    "이렇다", "그렇다", "저렇다",
    "잘못", "잘못하다",
    "순간적",
}

# Advanced POS heuristics: certain POS types tend to be higher-level
ADVANCED_POS_BONUS = {
    "noun": 0.0,
    "verb": 0.0,
    "adjective": 0.0,
    "adverb": 0.5,   # Adverbs tend to be more advanced
    "phrase": 0.5,
    "unknown": 0.0,
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
    difficulty_score: float = 4.0
    difficulty_estimated: bool = False
    source_fragment: str = ""


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
    target_level_num = _target_level_to_num(target_level)
    scored = []
    seen_families = {}  # Track word families to avoid duplicates

    for candidate in candidates:
        # Estimate difficulty first so dictionary-provided levels can refine ranking.
        difficulty_score, difficulty_estimated = _estimate_difficulty(candidate)

        # Dictionary lookup (if available)
        glosses = []
        definition = None
        level = None
        if dictionary_lookup:
            try:
                glosses, definition, level = dictionary_lookup(candidate.lemma)
                # If dictionary gives us a level, refine difficulty
                if level and level != "unknown":
                    dict_level_num = TOPIK_LEVELS.get(level, 4)
                    difficulty_score = float(dict_level_num)
                    difficulty_estimated = False
            except Exception as exc:
                logger.debug(
                    "Dictionary lookup fallback for lemma=%s (error=%s)",
                    candidate.lemma,
                    type(exc).__name__,
                )
                pass  # Degraded mode: continue without dictionary data

        score = _compute_score_from_difficulty(
            candidate, target_level_num, seen_families, difficulty_score
        )

        if score <= 0:
            continue

        reason = _generate_reason(candidate, score, target_level, difficulty_score)

        # Pick shortest useful fragment
        fragment = _pick_shortest_fragment(candidate)

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
                difficulty_score=difficulty_score,
                difficulty_estimated=difficulty_estimated,
                source_fragment=fragment,
            )
        )

    # Sort by score (descending)
    scored.sort(key=lambda c: c.score, reverse=True)

    return scored[:word_count]


def _target_level_to_num(target_level: str) -> float:
    """Convert target level to numeric value for scoring."""
    if target_level == "ANY":
        return 4.5  # Prefer intermediate/advanced
    return float(TOPIK_LEVELS.get(target_level, 4))


def _estimate_difficulty(candidate: LemmaCandidate) -> tuple[float, bool]:
    """Estimate difficulty score (1-6) for a candidate.

    Returns (difficulty_score, estimated_flag).
    Uses POS heuristics and word properties.
    """
    lemma = candidate.lemma
    pos = candidate.pos
    estimated = True

    # Base difficulty by POS
    base = 3.0  # Default intermediate

    if pos == "adverb":
        base = 4.5  # Adverbs tend to be more advanced
    elif pos == "noun":
        # Sino-Korean nouns tend to be more advanced
        if _has_sino_korean(lemma):
            base = 4.0
        else:
            base = 2.5
    elif pos == "verb":
        # Compound verbs tend to be more advanced
        if _is_compound_verb(lemma):
            base = 4.0
        else:
            base = 3.0
    elif pos == "adjective":
        base = 3.5

    # Length heuristic: longer words tend to be more advanced
    if len(lemma) >= 4:
        base += 0.5
    if len(lemma) >= 5:
        base += 0.5

    # Basic words are easy
    if lemma in BASIC_WORDS:
        base = 1.5

    return min(max(base, 1.0), 6.0), estimated


def _has_sino_korean(lemma: str) -> bool:
    """Heuristic: check if lemma looks Sino-Korean (Hanja-derived)."""
    # Common Sino-Korean characters that appear in Hangul romanization
    # This is a rough heuristic based on word patterns
    sino_indicators = ["적", "적", "력", "성", "관", "념", "률", "도", "화", "적"]
    return any(ind in lemma for ind in sino_indicators)


def _is_compound_verb(lemma: str) -> bool:
    """Check if a verb is a compound (typically more advanced)."""
    if not lemma.endswith("다"):
        return False
    stem = lemma[:-1]
    # Compound verbs often have multiple morphemes
    return len(stem) >= 4


def _compute_score_from_difficulty(
    candidate: LemmaCandidate,
    target_level_num: float,
    seen_families: dict,
    difficulty_score: float,
) -> float:
    """Compute ranking score using a finalized difficulty score."""
    score = 0.0

    # 1. Level fit score (MAJOR factor)
    # How well does this word's difficulty match the target level?
    level_diff = abs(difficulty_score - target_level_num)
    if level_diff <= 1.0:
        level_fit_score = 5.0 - level_diff * 2.0  # Perfect match = 5.0
    elif level_diff <= 2.0:
        level_fit_score = 3.0 - (level_diff - 1.0) * 1.5
    else:
        level_fit_score = max(0.0, 1.5 - (level_diff - 2.0))
    score += level_fit_score * 4.0

    # 2. Difficulty score contribution
    score += difficulty_score * 1.5

    # 3. Content POS score
    pos_score = POS_SCORES.get(candidate.pos, 1.0)
    score += pos_score * 1.0

    # 4. POS-based difficulty bonus
    pos_difficulty_bonus = ADVANCED_POS_BONUS.get(candidate.pos, 0.0)
    score += pos_difficulty_bonus * 2.0

    # 5. Frequency score (log scale, REDUCED weight to avoid easy word dominance)
    freq_score = min(math.log2(candidate.frequency + 1), 2.0)
    score += freq_score * 0.8

    # 6. Source sentence quality
    sentence = candidate.first_sentence
    if 10 <= len(sentence) <= 80:
        score += 1.0
    elif len(sentence) > 80:
        score += 0.3  # Too long is less useful

    # --- Penalties ---

    # TOO EASY penalty (CRITICAL for high levels)
    if candidate.lemma in BASIC_WORDS:
        if target_level_num >= 6.0:
            score -= 20.0  # Extremely strong penalty for TOPIK II 6
        elif target_level_num >= 5.0:
            score -= 12.0  # Very strong penalty for TOPIK II 5
        elif target_level_num >= 4.0:
            score -= 7.0  # Strong penalty for TOPIK II 4
        elif target_level_num >= 3.0:
            score -= 4.0  # Moderate penalty for TOPIK II 3
        else:
            score -= 2.0  # Light penalty for ANY/low levels

    # Proper name penalty
    if candidate.lemma.isalpha() and len(candidate.lemma) > 3:
        if candidate.pos == "noun" and candidate.frequency == 1:
            score -= 2.0

    # Duplicate family penalty
    family = _get_word_family(candidate.lemma)
    if family in seen_families:
        score -= 2.0  # Penalize variants of the same word
    seen_families[family] = candidate.lemma

    return max(score, 0)


def _get_word_family(lemma: str) -> str:
    """Get the word family for duplicate detection.

    Groups related words: 먹다, 먹었다, 먹어요 -> 먹다
    """
    # Strip common verb endings to get the root
    for ending in ["하다", "지다", "이다"]:
        if lemma.endswith(ending):
            return lemma[: -len(ending)]
    return lemma


def _pick_shortest_fragment(candidate: LemmaCandidate) -> str:
    """Pick the shortest useful Korean fragment containing the target word.

    Strategy:
    1. Find the surface form in the sentence
    2. Extract a compact window around that surface form
    3. Truncate long fragments at a word boundary when possible
    """
    if not candidate.all_sentences:
        return candidate.first_sentence

    # Use the first sentence as source
    sentence = candidate.first_sentence
    surface = candidate.surface_forms[0] if candidate.surface_forms else candidate.lemma

    # Try to extract a shorter fragment
    fragment = _extract_fragment(sentence, surface, candidate.lemma)
    if fragment:
        return fragment

    return sentence


def _extract_fragment(sentence: str, surface: str, lemma: str) -> str:
    """Extract shortest useful fragment containing the target word.

    Strategy: extract a window around the target word, respecting word
    boundaries. Max length ~45 chars to keep output concise.
    """
    max_len = 45

    # Find the position of the surface form in the sentence
    surface_pos = sentence.find(surface)
    if surface_pos < 0:
        # Truncate long sentences
        if len(sentence) > max_len:
            return sentence[:max_len].rstrip() + "…"
        return sentence

    # Window around the target word
    window_before = 20
    window_after = 20
    start = max(0, surface_pos - window_before)
    end = min(len(sentence), surface_pos + len(surface) + window_after)

    # Adjust start to word boundary (space or beginning)
    while start > 0 and sentence[start - 1] not in " .?!,:;…\n":
        start -= 1
        if start <= max(0, surface_pos - window_before - 5):
            break
    # Don't start mid-word: skip back to space if we're in the middle
    if start > 0 and sentence[start] not in " .?!,:;…\n":
        # Find previous space
        prev_space = sentence.rfind(" ", 0, start)
        if prev_space >= 0:
            start = prev_space + 1

    # Adjust end to word boundary
    while end < len(sentence) and sentence[end] not in " .?!,:;…\n":
        end += 1
        if end >= min(len(sentence), surface_pos + len(surface) + window_after + 5):
            break

    fragment = sentence[start:end].strip()

    # If still too long, hard truncate at word boundary
    if len(fragment) > max_len:
        trunc_pos = fragment.rfind(" ", 0, max_len)
        if trunc_pos > 10:
            fragment = fragment[:trunc_pos].rstrip() + "…"
        else:
            fragment = fragment[:max_len].rstrip() + "…"

    # If too short, just return the window
    if len(fragment) < 3:
        return sentence[max(0, surface_pos - 5):surface_pos + len(surface) + 10].strip()

    return fragment


def _generate_reason(
    candidate: LemmaCandidate,
    score: float,
    target_level: str,
    difficulty_score: float,
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

    target_num = _target_level_to_num(target_level)
    level_diff = abs(difficulty_score - target_num)
    if level_diff <= 0.5:
        parts.append("matches target level")
    elif level_diff <= 1.5:
        parts.append("near target level")

    if score > 15:
        parts.append("high-priority vocabulary")
    elif score > 8:
        parts.append("useful for comprehension")

    return ". ".join(parts) if parts else "Selected vocabulary item"
