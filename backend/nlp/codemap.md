# backend/nlp/

## Responsibility
Korean NLP pipeline: morphological analysis, sentence splitting, candidate filtering, lemmatization, and ranking. Core engine for extracting study-ready vocabulary from raw Korean text.

## Design
- **Pipeline Pattern**: `ExtractionPipeline` orchestrates stages 1-5 (normalize → split → tokenize → filter → merge).
- **Morphological Tokenizer**: `KoreanTokenizer` wraps `kiwipiepy.Kiwi` for morphology-aware tokenization. Groups Kiwi morphemes into word-level tokens using character offset gaps.
- **POS-Based Filtering**: `filter.py` uses Kiwi POS tag sets (`NOUN_TAGS`, `VERB_TAGS`, etc.) + deny list (`DROP_TOKENS`) to keep only content words.
- **Lemma Merging**: `lemmatizer.py` groups tokens by lemma, tracking frequency and source sentences. Maps Kiwi POS tags to simplified POS (noun/verb/adjective/adverb).
- **Multi-Factor Ranking**: `ranker.py` scores candidates using frequency (log scale), POS weight, sentence quality, with penalties for basic words and duplicate families.

## Modules
| File | Responsibility |
|------|----------------|
| `pipeline.py` | Orchestration: normalize → split → tokenize → filter → merge |
| `splitter.py` | Sentence boundary detection via regex on `.!?…` and Korean quotes |
| `tokenizer.py` | Kiwi morphological analysis, morpheme grouping, lemma reconstruction |
| `filter.py` | POS-based filtering + deny list for particles/endings |
| `lemmatizer.py` | Lemma merging, POS mapping, `LemmaCandidate` dataclass |
| `ranker.py` | Multi-factor scoring, word family dedup, `RankedCandidate` dataclass |

## Lemma Reconstruction Patterns
- `NNG + XSV(하)` → `~하다` (당황하다)
- `NNG + VV/VA` → `~다` (살해당하다)
- `VV` → `stem + 다` (망설이다, 먹다)
- `VV/R` → `stem + 다` (compound verbs)
- `하 + EC + VX(지)` → `~지다` with vowel harmony (해지다)

## Integration
- Consumed by: `api/extract_vocab.py`
- Depends on: `kiwipiepy` (Kiwi)
