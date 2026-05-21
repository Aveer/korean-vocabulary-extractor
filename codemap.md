# Repository Atlas: korean-vocab-extractor

## Project Responsibility
Korean vocabulary extraction and sentence-mining study app. Users paste Korean text, receive study-ready vocabulary cards with English glosses/source context/TOPIK level information, save cards to a local deck, review due cards, and track local XP/streak progress.

**Status**: Study-game MVP complete (2026-05-21). 40 tests passing.

## System Entry Points
- `frontend/src/main.tsx` — React application bootstrap
- `backend/main.py` — FastAPI server entry point
- `backend/api/extract_vocab.py` — Core extraction endpoint (`POST /api/extract-vocab`)
- `backend/api/study.py` — Local deck/review/progress endpoints (`/api/study/*`)
- `AGENTS.md` — Agent instructions and critical constraints

## Architecture

### Frontend (React + Vite + TypeScript)
- Extract / Deck / Review / Progress tabs
- Text input area for Korean passages with TOPIK II level selector and quest size
- Known/ignored filters → calls `POST /api/extract-vocab`
- Results display with save/known/ignore actions, reading highlights, copy/export actions (CSV, Anki CSV)
- Local deck browser, review reveal/rating flow, XP/streak/progress panels

### Backend (Python FastAPI)
- `POST /api/extract-vocab` endpoint
- `/api/study/*` endpoints backed by local SQLite in OS app data
- 9-stage extraction pipeline:
  1. Input normalization
  2. Korean sentence splitting
  3. Morphological analysis via `kiwipiepy`
  4. Candidate filtering (keep content words, drop particles/endings)
  5. Lemmatization to dictionary forms
  6. Duplicate lemma merging
  7. Dictionary lookup (bundled offline provider or optional NIKL API with local cache)
  8. TOPIK level matching
  9. Deterministic ranking + formatting, plus optional study-status filtering/annotation

### Korean NLP
- `kiwipiepy` (Kiwi) for morphology-aware parsing
- Required for proper lemmatization (e.g., `당황했다` → `당황하다`)
- Regex/whitespace tokenization is NOT sufficient

### Dictionary
- Default: bundled offline Korean-English dictionary (`backend/dictionary/bundled_dict.json`)
- Optional: National Institute of Korean Language Korean-English Learners' Dictionary API
- API key via settings or `KRDICT_API_KEY` env var
- Degraded/offline mode: works without API key via bundled dictionary
- Local JSON cache/config under OS app data via `backend/config_paths.py`

### Study Data
- Local SQLite database (`study.sqlite3`) under OS app data via `backend/config_paths.py`
- `KVE_DATA_DIR` override for tests/package smoke runs
- Persists explicit saved card fields, lemma known/ignored status, review logs, XP/streak stats
- Raw pasted passages are not stored during extraction

## Directory Map
| Directory | Responsibility | Detailed Map |
|-----------|----------------|--------------|
| `backend/` | FastAPI backend server orchestrating the extraction pipeline | [View Map](backend/codemap.md) |
| `backend/api/` | API endpoints, Pydantic models, pipeline orchestration | [View Map](backend/api/codemap.md) |
| `backend/nlp/` | Korean NLP: Kiwi tokenization, sentence splitting, filtering, lemmatization, ranking | [View Map](backend/nlp/codemap.md) |
| `backend/dictionary/` | Dictionary provider abstraction, NIKL API integration, degraded-mode support | [View Map](backend/dictionary/codemap.md) |
| `backend/cache/` | JSON file-based dictionary cache with LRU-like eviction | [View Map](backend/cache/codemap.md) |
| `backend/study/` | Local SQLite deck, lemma statuses, SRS scheduling, stats | [View Map](backend/study/codemap.md) |
| `frontend/` | React + Vite + TypeScript SPA | [View Map](frontend/codemap.md) |
| `frontend/src/` | Application source: App component, state management, API calls | [View Map](frontend/src/codemap.md) |
| `frontend/src/components/` | VocabCard display, reading highlights, ExportActions (copy, CSV, Anki CSV) | [View Map](frontend/src/components/codemap.md) |
| `frontend/src/types/` | TypeScript interfaces mirroring backend Pydantic models | [View Map](frontend/src/types/codemap.md) |
| `tests/` | pytest test suite: 40 tests covering pipeline, ranking, degraded mode, env loading, translation opt-out, study DB/API, API contracts | [View Map](tests/codemap.md) |
| `docs/` | Archival: original implementation plan and agent prompt | [View Map](docs/codemap.md) |

## Critical Constraints
- Use `TOPIK` never `Topic`. Levels: `TOPIK_II_3`–`TOPIK_II_6` plus `ANY`
- Dictionary API key env var: `KRDICT_API_KEY`
- Do NOT use DuckDuckGo as primary dictionary source
- Do NOT expose `KRDICT_API_KEY` to frontend
- Do NOT permanently store pasted passages during extraction; explicit saved cards may store their source fragment/sentence
- Do NOT send pasted text to third-party LLM APIs without explicit opt-in
- Packaged builds must include `frontend/dist`, `backend/dictionary/bundled_dict.json`, and `kiwipiepy_model`; verify with `python scripts/build_package.py --clean`

## Running
```bash
# Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Tests
pytest tests/ -v

# Packaged app build + smoke test
python scripts/build_package.py --clean
```
