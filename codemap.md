# Repository Atlas: korean-vocab-extractor

## Project Responsibility
Korean vocabulary extraction study app. Users paste Korean text and receive study-ready vocabulary cards with English glosses, source sentences, and TOPIK level information.

**Status**: MVP complete (2026-04-30). All features implemented, 26 tests passing.

## System Entry Points
- `frontend/src/main.tsx` — React application bootstrap
- `backend/main.py` — FastAPI server entry point
- `backend/api/extract_vocab.py` — Core extraction endpoint (`POST /api/extract-vocab`)
- `AGENTS.md` — Agent instructions and critical constraints

## Architecture

### Frontend (React + Vite + TypeScript)
- Text input area for Korean passages
- TOPIK II level selector (levels 3–6 + ANY)
- Word count input (1–100, default 20)
- Extract button → calls `POST /api/extract-vocab`
- Results display with copy/export actions (CSV, Anki CSV)

### Backend (Python FastAPI)
- `POST /api/extract-vocab` endpoint
- 9-stage extraction pipeline:
  1. Input normalization
  2. Korean sentence splitting
  3. Morphological analysis via `kiwipiepy`
  4. Candidate filtering (keep content words, drop particles/endings)
  5. Lemmatization to dictionary forms
  6. Duplicate lemma merging
  7. Dictionary lookup (NIKL API with local cache)
  8. TOPIK level matching
  9. Deterministic ranking + formatting

### Korean NLP
- `kiwipiepy` (Kiwi) for morphology-aware parsing
- Required for proper lemmatization (e.g., `당황했다` → `당황하다`)
- Regex/whitespace tokenization is NOT sufficient

### Dictionary
- Primary: National Institute of Korean Language Korean-English Learners' Dictionary API
- API key via `KRDICT_API_KEY` env var
- Degraded mode: works without API key (glosses may be empty)
- Local JSON cache for dictionary lookups by lemma

## Directory Map
| Directory | Responsibility | Detailed Map |
|-----------|----------------|--------------|
| `backend/` | FastAPI backend server orchestrating the extraction pipeline | [View Map](backend/codemap.md) |
| `backend/api/` | API endpoints, Pydantic models, pipeline orchestration | [View Map](backend/api/codemap.md) |
| `backend/nlp/` | Korean NLP: Kiwi tokenization, sentence splitting, filtering, lemmatization, ranking | [View Map](backend/nlp/codemap.md) |
| `backend/dictionary/` | Dictionary provider abstraction, NIKL API integration, degraded-mode support | [View Map](backend/dictionary/codemap.md) |
| `backend/cache/` | JSON file-based dictionary cache with LRU-like eviction | [View Map](backend/cache/codemap.md) |
| `frontend/` | React + Vite + TypeScript SPA | [View Map](frontend/codemap.md) |
| `frontend/src/` | Application source: App component, state management, API calls | [View Map](frontend/src/codemap.md) |
| `frontend/src/components/` | VocabCard display, ExportActions (copy, CSV, Anki CSV) | [View Map](frontend/src/components/codemap.md) |
| `frontend/src/types/` | TypeScript interfaces mirroring backend Pydantic models | [View Map](frontend/src/types/codemap.md) |
| `tests/` | pytest test suite: 26 tests covering pipeline, ranking, degraded mode, API | [View Map](tests/codemap.md) |
| `docs/` | Archival: original implementation plan and agent prompt | [View Map](docs/codemap.md) |

## Critical Constraints
- Use `TOPIK` never `Topic`. Levels: `TOPIK_II_3`–`TOPIK_II_6` plus `ANY`
- Dictionary API key env var: `KRDICT_API_KEY`
- Do NOT use DuckDuckGo as primary dictionary source
- Do NOT expose `KRDICT_API_KEY` to frontend
- Do NOT permanently store pasted passages
- Do NOT send pasted text to third-party LLM APIs without explicit opt-in

## Running
```bash
# Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Tests
pytest tests/ -v
```
