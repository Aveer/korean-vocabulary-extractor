# backend/

## Responsibility
Python FastAPI backend server. Orchestrates the Korean vocabulary extraction pipeline, exposing a REST API for the frontend to consume.

## Design
- **FastAPI Application**: `main.py` bootstraps the app with CORS middleware and mounts the extract-vocab router at `/api`.
- **Lazy Initialization**: Pipeline and dictionary provider are lazily initialized on first request to avoid blocking startup.
- **Modular Architecture**: Clean separation into `api/` (endpoints + models), `nlp/` (morphological analysis pipeline), `dictionary/` (dictionary lookup), and `cache/` (persistence).

## Flow
1. `main.py` creates FastAPI app, adds CORS, mounts `/api` router
2. Incoming `POST /api/extract-vocab` → `extract_vocab.py` handler
3. Handler delegates to `ExtractionPipeline.extract()` (stages 1-5)
4. Handler runs `rank_candidates()` with dictionary lookup (stages 6-9)
5. Response formatted as `ExtractVocabResponse` with `VocabCard[]` + `ExtractMeta`

## Integration
- Consumed by: Frontend (`frontend/src/App.tsx`) via `/api/extract-vocab`
- Depends on: `kiwipiepy` (Kiwi), `httpx`, `pydantic`, `fastapi`, `uvicorn`
- Sub-modules: `api/`, `nlp/`, `dictionary/`, `cache/`
