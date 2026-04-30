"""Candidate filtering for vocabulary extraction.

Filters tokens using Kiwi POS tags.
"""

from nlp.tokenizer import Token, NOUN_TAGS, VERB_TAGS, ADJECTIVE_TAGS, ADVERB_TAGS, CONTENT_TAGS


# Minimum surface form length to consider
MIN_SURFACE_LENGTH = 1

# Tokens to always drop regardless of POS
DROP_TOKENS = {
    # Particles
    "이", "가", "를", "을", "는", "도", "에", "에서", "으로", "으로부터",
    "에게", "부터", "까지", "와", "과", "하고", "랑",
    "의", "로", "러", "여",
    # Common fillers / grammar
    "아", "어", "여", "지", "다", "네", "냐", "까",
    "야",
    # Extremely common words (too basic)
    "할", "thing",
}


def filter_candidates(tokens: list[Token]) -> list[Token]:
    """Filter tokens to keep only useful vocabulary candidates.

    Keeps: nouns, verbs, adjectives, adverbs, Sino-Korean terms
    Drops: particles, endings, punctuation, numbers, auxiliaries
    """
    filtered = []
    for token in tokens:
        if _should_drop(token):
            continue
        filtered.append(token)
    return filtered


def _should_drop(token: Token) -> bool:
    """Check if a token should be dropped."""
    # Drop by POS - keep only content-bearing tags
    if token.pos not in CONTENT_TAGS:
        return True

    # Drop very short tokens (usually particles or grammar)
    if len(token.surface) < MIN_SURFACE_LENGTH:
        return True

    # Drop known grammar tokens
    if token.surface in DROP_TOKENS:
        return True

    # Drop pure numbers
    if token.surface.isdigit():
        return True

    # Drop single-character tokens that are likely particles
    # (but keep single-character nouns/verbs)
    if len(token.surface) == 1 and token.pos not in NOUN_TAGS | VERB_TAGS | ADJECTIVE_TAGS:
        return True

    return False
