"""Korean morphological analysis using kiwipiepy.

Groups Kiwi morphemes into word-level tokens and reconstructs
dictionary forms.
"""

from dataclasses import dataclass

from kiwipiepy import Kiwi


@dataclass
class Token:
    """A word-level vocabulary token."""

    surface: str  # Original surface form
    lemma: str  # Reconstructed dictionary form
    pos: str  # Kiwi POS tag
    sentence_index: int
    sentence_text: str


# Kiwi POS tag categories
NOUN_TAGS = {"NNG", "NNP", "NR", "SL", "SN"}
VERB_TAGS = {"VV", "VV-R", "VX", "XSV", "VCP", "VCC", "VS"}
ADJECTIVE_TAGS = {"VA", "XSA"}
ADVERB_TAGS = {"MAG", "MAJ", "IC"}
CONTENT_TAGS = NOUN_TAGS | VERB_TAGS | ADJECTIVE_TAGS | ADVERB_TAGS

# Clause-connecting endings (word boundaries)
CLAUSE_CONNECTORS = {"지만", "면서", "다가", "려면", "니까", "라서", "므로"}


class KoreanTokenizer:
    """Korean morphological tokenizer using kiwipiepy."""

    def __init__(self):
        self._kiwi: Kiwi | None = None

    @property
    def kiwi(self) -> Kiwi:
        if self._kiwi is None:
            self._kiwi = Kiwi()
        return self._kiwi

    def tokenize_sentences(self, sentences: list[str]) -> list[Token]:
        """Tokenize sentences into word-level tokens."""
        tokens = []
        for idx, sentence in enumerate(sentences):
            sentence_tokens = self._extract_tokens(sentence, idx)
            tokens.extend(sentence_tokens)
        return tokens

    def _extract_tokens(self, sentence: str, sentence_index: int) -> list[Token]:
        """Extract all content-bearing tokens from a sentence."""
        result = self.kiwi.analyze(sentence, top_n=1)
        if not result:
            return []

        morphemes, _ = result[0]

        # Group morphemes into words using character offsets
        groups = self._group_by_word(morphemes)

        tokens = []
        for group in groups:
            token = self._group_to_token(group, sentence, sentence_index)
            if token:
                tokens.append(token)
        return tokens

    def _group_by_word(self, morphemes) -> list[list]:
        """Group morphemes into words using character position gaps.

        Words are separated by spaces or punctuation in the original text.
        We detect word boundaries by finding gaps in character positions.
        """
        if not morphemes:
            return []

        groups = []
        current_group = [morphemes[0]]

        for i in range(1, len(morphemes)):
            prev = morphemes[i - 1]
            curr = morphemes[i]

            # Calculate where the previous morpheme ends
            prev_end = prev.start + prev.len

            # If there's a gap, it's a word boundary
            if curr.start > prev_end:
                groups.append(current_group)
                current_group = [curr]
            else:
                current_group.append(curr)

        if current_group:
            groups.append(current_group)

        return groups

    def _group_to_token(self, morphemes: list, sentence: str, sentence_index: int) -> Token | None:
        """Convert a morpheme group into a single token."""
        if not morphemes:
            return None

        # Find content morphemes in this group
        content_morphs = [m for m in morphemes if m.tag in CONTENT_TAGS]

        if not content_morphs:
            return None

        # Use the first content morpheme as the primary
        primary = content_morphs[0]

        # Reconstruct the surface form from all morpheme forms
        surface = "".join(m.form for m in morphemes if m.tag not in ("SF", "SS", "SY", "SP", "SES", "SE", "SO", "SH", "SW"))

        # Reconstruct the lemma
        lemma = self._reconstruct_lemma(morphemes, content_morphs)

        return Token(
            surface=surface,
            lemma=lemma,
            pos=primary.tag,
            sentence_index=sentence_index,
            sentence_text=sentence,
        )

    def _reconstruct_lemma(self, morphemes: list, content_morphs: list) -> str:
        """Reconstruct dictionary form from morphemes.

        Patterns handled:
        - NNG + XSV(하) -> ~하다 (당황하다)
        - NNG + VV(당하) -> ~당하다 (살해당하다)
        - VV + endings -> ~다 (망설이다, 돌려받다)
        - VV/R + 어/아 + 지 + endings -> root ~다 (느끼다)
        - 하(VV/XSA) + 어/아 + 지 + endings -> ~지다 (해지다)
        """
        if not content_morphs:
            return ""

        primary = content_morphs[0]
        tag = primary.tag
        stem = primary.form

        # Noun + 하다 pattern: NNG followed by XSV(하)
        if tag in NOUN_TAGS and len(content_morphs) >= 2:
            next_content = content_morphs[1]
            if next_content.tag == "XSV":
                return stem + "하다"
            # Noun + VV pattern (e.g., 살해(NNG) + 당하(VV) -> 살해당하다)
            if next_content.tag in ("VV", "VA"):
                return stem + next_content.form + "다"

        # Compound verbs (VV-R): add 다
        if tag == "VV-R":
            return stem + "다"

        # Check for 하 + 어/아 + 지 pattern -> ~지다 (해지다, 해산하다, etc.)
        # This handles both VV and XSA tags for 하
        has_ji = any(m.tag == "VX" and m.form == "지" for m in morphemes)
        if has_ji and stem == "하" and tag in ("VV", "XSA", "XSV"):
            for m in morphemes:
                if m.tag == "EC":
                    surface = self._apply_vowel_harmony(stem, m.form)
                    return surface + "지다"

        # Verbs and adjectives: add 다
        if tag in VERB_TAGS | ADJECTIVE_TAGS:
            return stem + "다"

        # Nouns: use as-is
        return stem

    def _apply_vowel_harmony(self, stem: str, ending: str) -> str:
        """Apply Korean vowel harmony for stem + ending.

        하 + 어 -> 해
        하 + 아 -> 하아 (rare)
        """
        if stem == "하" and ending == "어":
            return "해"
        if stem == "하" and ending == "아":
            return "하아"
        return stem + ending

    def tokenize_text(self, text: str) -> tuple[list[str], list[Token]]:
        """Tokenize raw text: split into sentences, then tokenize."""
        from nlp.splitter import split_sentences
        sentences = split_sentences(text)
        tokens = self.tokenize_sentences(sentences)
        return sentences, tokens
