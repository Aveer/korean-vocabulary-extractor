"""Korean sentence splitting."""

import re


def split_sentences(text: str) -> list[str]:
    """Split Korean text into sentences.

    Handles Korean sentence-ending punctuation and common endings:
    . ? ! … " 다. 요. 죠. etc.

    Returns list of non-empty sentence strings.
    """
    # Split on sentence boundaries: Korean/English punctuation
    # Keep the delimiter with the sentence
    sentences = re.split(r'(?<=[.!?…!?])\s*', text)

    # Also split on Korean quotation marks that end sentences
    result = []
    for sentence in sentences:
        # Further split on closing quotes if they contain multiple sentences
        parts = re.split(r'(?<=["])\s*', sentence)
        result.extend(parts)

    # Clean up: strip and filter empty
    result = [s.strip() for s in result if s.strip()]

    return result
