"""Full Korean NLP extraction pipeline.

Combines sentence splitting, tokenization, filtering, and lemmatization
into a single pipeline.
"""

from nlp.splitter import split_sentences
from nlp.tokenizer import KoreanTokenizer
from nlp.filter import filter_candidates
from nlp.lemmatizer import merge_by_lemma, LemmaCandidate


class ExtractionPipeline:
    """9-stage extraction pipeline for Korean vocabulary.

    Stages:
    1. Input normalization
    2. Sentence splitting
    3. Morphological analysis (Kiwi)
    4. Candidate filtering
    5. Lemmatization & merging
    6-9. Dictionary lookup, TOPIK matching, ranking (handled by API layer)
    """

    def __init__(self):
        self.tokenizer = KoreanTokenizer()

    def extract(self, text: str) -> tuple[list[str], list[LemmaCandidate]]:
        """Run the extraction pipeline on Korean text.

        Args:
            text: Raw Korean text to extract vocabulary from.

        Returns:
            Tuple of (sentences, lemma_candidates).
            lemma_candidates are filtered, lemmatized, and merged.
        """
        # Stage 1: Normalize input
        normalized = _normalize(text)

        # Stage 2: Sentence splitting
        sentences = split_sentences(normalized)

        # Stage 3: Morphological analysis
        tokens = self.tokenizer.tokenize_sentences(sentences)

        # Stage 4: Candidate filtering
        candidates = filter_candidates(tokens)

        # Stage 5: Lemmatization & merging
        lemma_candidates = merge_by_lemma(candidates)

        return sentences, lemma_candidates


def _normalize(text: str) -> str:
    """Normalize input text.

    - Trim whitespace
    - Normalize repeated whitespace
    - Preserve Korean punctuation
    """
    if not text or not text.strip():
        raise ValueError("Input text is empty")

    # Trim and normalize whitespace
    normalized = text.strip()
    normalized = " ".join(normalized.split())

    return normalized
