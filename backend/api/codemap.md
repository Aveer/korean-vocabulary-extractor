# backend/api/

## Responsibility
API layer: HTTP endpoints, request/response models, pipeline orchestration, dictionary settings, and local study endpoints. Serves as the boundary between external clients and internal NLP/dictionary/study modules.

## Design
- **APIRouter Pattern**: `extract_vocab.py` defines extraction/dictionary routes mounted at `/api`; `study.py` defines local study routes mounted at `/api/study`.
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
4. Filter known/ignored lemmas and annotate `studyStatus`/`savedCardId` from `study.service`
5. Return `ExtractVocabResponse(cards, meta)`

Study flow:
1. `POST /api/study/cards` saves explicit card fields idempotently to local SQLite
2. `PUT /api/study/lemmas/{lemma}/status` marks lemmas new/known/ignored
3. `GET /api/study/reviews/due` and `POST /api/study/reviews/{card_id}` drive SRS review
4. `GET /api/study/stats` returns deck/due/known/ignored/streak/XP/level stats

## Models
- `ExtractVocabRequest`: text, targetLevel, wordCount, includeSentenceTranslation, excludeKnown, excludeIgnored
- `VocabCard`: lemma, display, pos, englishGlosses, koreanDefinition, sourceSentence, level, frequencyInText, reason, studyStatus, savedCardId
- `ExtractMeta`: inputLength, candidateCount, returnedCount, dictionaryProvider
- `ExtractVocabResponse`: cards[], meta
- `DictionaryConfigResponse`: provider, apiKeySet, bundledAvailable, bundledEntryCount, bundledSource
- Study models: card save/list responses, lemma status, due reviews, review results, stats

## Integration
- Consumed by: Frontend via HTTP
- Depends on: `nlp.pipeline.ExtractionPipeline`, `nlp.ranker.rank_candidates`, `dictionary.provider.create_provider`, `study.service`
