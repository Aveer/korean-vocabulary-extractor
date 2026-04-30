# backend/api/

## Responsibility
API layer: HTTP endpoints, request/response models, and pipeline orchestration. Serves as the boundary between external clients and internal NLP/dictionary modules.

## Design
- **APIRouter Pattern**: `extract_vocab.py` defines a FastAPI `APIRouter` mounted at `/api` prefix.
- **Pydantic Models**: `models.py` defines strongly-typed request/response schemas with camelCase JSON aliases (`populate_by_name=True`).
- **Lazy Singleton**: `_pipeline` and `_provider` are module-level singletons initialized on first access.
- **Error Handling**: `HTTPException` for 400/500 errors; ValueError from pipeline caught and converted to 400.

## Flow
1. `POST /api/extract-vocab` receives `ExtractVocabRequest`
2. Input validation: non-empty text, max 100K characters
3. `_extract()` orchestrates:
   - `pipeline.extract(text)` → sentences + lemma candidates
   - `rank_candidates()` with optional dictionary lookup → ranked candidates
   - Map `RankedCandidate` → `VocabCard`
4. Return `ExtractVocabResponse(cards, meta)`

## Models
- `ExtractVocabRequest`: text, targetLevel, wordCount, includeSentenceTranslation
- `VocabCard`: lemma, display, pos, englishGlosses, koreanDefinition, sourceSentence, level, frequencyInText, reason
- `ExtractMeta`: inputLength, candidateCount, returnedCount, dictionaryProvider
- `ExtractVocabResponse`: cards[], meta

## Integration
- Consumed by: Frontend via HTTP
- Depends on: `nlp.pipeline.ExtractionPipeline`, `nlp.ranker.rank_candidates`, `dictionary.provider.create_provider`
