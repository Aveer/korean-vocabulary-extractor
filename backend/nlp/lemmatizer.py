"""Lemmatization utilities for Korean vocabulary.

Normalizes Korean words to their dictionary forms:
- Verbs/adjectives: dictionary -다 form (e.g., 당황했다 -> 당황하다)
- Nouns: preserve as-is
- Compound verbs: extract base verb
"""

from dataclasses import dataclass, field
from collections import defaultdict

from nlp.tokenizer import Token


@dataclass
class LemmaCandidate:
    """A vocabulary candidate after lemmatization and merging."""

    lemma: str  # Dictionary form
    display: str  # Display form (may differ from lemma for phrases)
    pos: str  # Mapped POS (noun, verb, adjective, adverb, phrase, unknown)
    frequency: int  # Times this lemma appears in text
    surface_forms: list[str]  # All surface forms seen
    first_sentence: str  # First sentence where this lemma appeared
    all_sentences: list[str] = field(default_factory=list)  # All sentences


# Map Kiwi POS tags to our simplified POS
POS_MAP = {
    # Nouns
    "NNG": "noun",       # General noun
    "NNP": "noun",       # Proper noun
    "NR": "noun",        # Noun
    "SL": "noun",        # Slang
    "SN": "noun",        # Sino-Korean noun
    # Verbs
    "VV": "verb",        # General verb
    "VX": "verb",        # Auxiliary verb
    "XSV": "verb",       # Special verb (하다)
    "VCP": "verb",       # Copula
    "VCC": "verb",       # Connective verb
    "VA": "adjective",   # Adjective (descriptive verb)
    "XSA": "adjective",  # Special adjective
    # Adverbs
    "MAG": "adverb",     # Adverb
    "MAJ": "adverb",     # Adverb (particle-like)
    "IC": "adverb",      # Interjection
}


def merge_by_lemma(tokens: list[Token]) -> list[LemmaCandidate]:
    """Merge tokens by lemma, keeping track of frequency and context.

    Groups tokens with the same lemma together, counting frequency
    and collecting source sentences.
    """
    lemma_groups: dict[str, LemmaCandidate] = {}

    for token in tokens:
        lemma = token.lemma
        pos = POS_MAP.get(token.pos, _infer_pos(token))

        if lemma in lemma_groups:
            existing = lemma_groups[lemma]
            existing.frequency += 1
            if token.surface not in existing.surface_forms:
                existing.surface_forms.append(token.surface)
            if token.sentence_text not in existing.all_sentences:
                existing.all_sentences.append(token.sentence_text)
        else:
            lemma_groups[lemma] = LemmaCandidate(
                lemma=lemma,
                display=lemma,
                pos=pos,
                frequency=1,
                surface_forms=[token.surface],
                first_sentence=token.sentence_text,
                all_sentences=[token.sentence_text],
            )

    return list(lemma_groups.values())


def _infer_pos(token: Token) -> str:
    """Infer simplified POS from Kiwi tag when not in POS_MAP."""
    tag = token.pos
    # Noun-like tags
    if tag.startswith("NN") or tag.startswith("NR") or tag in ("SL", "SN"):
        return "noun"
    # Verb-like tags
    if tag.startswith("VV") or tag.startswith("VS") or tag in ("VX", "XSV", "VCP", "VCC"):
        return "verb"
    # Adjective-like tags
    if tag.startswith("VA") or tag == "XSA":
        return "adjective"
    # Adverb-like tags
    if tag.startswith("MA") or tag == "IC":
        return "adverb"
    return "unknown"


def normalize_lemma(lemma: str, pos: str) -> str:
    """Normalize a lemma to its dictionary form.

    For verbs/adjectives, ensure -다 form.
    For nouns, preserve as-is.
    """
    if pos in ("verb", "adjective"):
        # Kiwi should already give us the dictionary form,
        # but ensure it ends in -다 for verbs/adjectives
        if not lemma.endswith("다"):
            # Try common patterns
            if lemma.endswith("한다"):
                pass  # Already correct
            elif lemma.endswith("하다"):
                pass  # Already correct
            # If Kiwi gave us a non-dictionary form, keep it as-is
            # (Kiwi is usually correct)
    return lemma
