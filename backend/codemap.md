# backend/

## Responsibility
Python FastAPI backend server. Orchestrates the Korean vocabulary extraction pipeline and local study-game persistence, exposing REST APIs for the frontend to consume.

## Design
- **FastAPI Application**: `main.py` bootstraps the app with CORS middleware and mounts extract-vocab and study routers under `/api`.
- **Lazy Initialization**: Pipeline and dictionary provider are lazily initialized on first request to avoid blocking startup.
- **Modular Architecture**: Clean separation into `api/` (endpoints + models), `nlp/` (morphological analysis pipeline), `dictionary/` (dictionary lookup), `cache/` (dictionary persistence), and `study/` (SQLite deck/review/progress).

## Flow
1. `main.py` creates FastAPI app, adds CORS, mounts `/api` extraction/dictionary routes and `/api/study` routes
2. Incoming `POST /api/extract-vocab` → `extract_vocab.py` handler
3. Handler delegates to `ExtractionPipeline.extract()` (stages 1-5)
4. Handler runs `rank_candidates()` with dictionary lookup (stages 6-9), then applies optional study-status filtering/annotation
5. Study requests go through `api/study.py` → `study/service.py` → `study/db.py` (`study.sqlite3` under app data)
6. Response formatted as `ExtractVocabResponse` with `VocabCard[]` + `ExtractMeta`, or study-specific responses

## Integration
- Consumed by: Frontend (`frontend/src/App.tsx`) via `/api/extract-vocab`, `/api/dictionary-config`, and `/api/study/*`
- Depends on: `kiwipiepy` (Kiwi), `httpx`, `pydantic`, `fastapi`, `uvicorn`
- Sub-modules: `api/`, `nlp/`, `dictionary/`, `cache/`, `study/`
