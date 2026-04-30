# Korean Vocab Extractor

Korean vocabulary extraction study app. Paste Korean text → get study-ready vocab cards.

## Stack

- **Frontend:** React + Vite + TypeScript
- **Backend:** Python FastAPI
- **Korean NLP:** `kiwipiepy` (Kiwi) — morphology-aware parsing is required; regex/whitespace tokenization is not enough
- **Dictionary:** Bundled offline (kengdic, 67K entries, `dictionary/bundled_dict.json`) + optional NIKL API. Switchable via settings.
- **Cache:** JSON file (`backend/cache_data/dictionary_cache.json`) with LRU-like eviction
- **Config:** `backend/cache_data/dictionary_config.json` — provider choice + API key

## Status

**MVP complete** (2026-04-30). All features implemented, 26 tests passing. Bundled offline dictionary + dark mode.

## Repository Map

A full codemap is available at `codemap.md` in the project root.

Before working on any task, read `codemap.md` to understand:
- Project architecture and entry points
- Directory responsibilities and design patterns
- Data flow and integration points between modules

## Architecture

### Backend (`backend/`)
- `main.py` — FastAPI app entry point, CORS, mounts `/api` router
- `api/` — Endpoints (`extract_vocab.py`), Pydantic models (`models.py`), pipeline orchestration
- `nlp/` — Kiwi morphological analysis, sentence splitting, candidate filtering, lemmatization, ranking
- `dictionary/` — BundledProvider (offline, 67K entries), NIKL API provider, config-driven switching
- `cache/` — Dictionary cache storage

### Frontend (`frontend/`)
- React + Vite + TypeScript
- Textarea, TOPIK level selector, word count input, extract button
- Vocab card results with copy, CSV export, Anki CSV export
- Settings panel: dictionary source selector, API key input, dark/light mode toggle
- Theme persisted in `localStorage`, dictionary config persisted on backend
- Proxies API calls to `http://localhost:8000`

### Pipeline (9 stages)
1. Normalize input → 2. Sentence split → 3. Kiwi tokenization → 4. Candidate filtering → 5. Lemmatization → 6. Duplicate merging → 7. Dictionary lookup → 8. TOPIK level matching → 9. Ranking & formatting

### Tests (`tests/`)
- 26 tests covering sentence splitting, lemmatization, filtering, merging, ranking, degraded mode, API endpoint

## Critical Constraints

- Use `TOPIK`, never `Topic`. Levels: `TOPIK_II_3` through `TOPIK_II_6` plus `ANY`.
- Dictionary API key env var: `KRDICT_API_KEY`. App must work in degraded mode without it (no crash, glosses may be empty).
- Do NOT use DuckDuckGo as primary dictionary source.
- Do NOT expose `KRDICT_API_KEY` to the frontend.
- Do NOT permanently store pasted passages. Dictionary cache by lemma is OK.
- Do NOT send pasted text to third-party LLM APIs without explicit opt-in.

## API

- `POST /api/extract-vocab` — full spec in `README.md` §API.
- `GET /api/dictionary-config` — current provider, bundled stats
- `PUT /api/dictionary-config` — switch provider, save API key

## Running

```bash
# All-in-one (starts both, kills both on Ctrl+C)
./dev.sh

# Or separately:
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# Tests
pytest tests/ -v
```

## Key Docs

- `README.md` — Setup, usage, API spec, pipeline explanation, limitations
- `docs/korean-vocab-extractor-plan.md` — Original implementation plan (archival)
- `docs/korean-vocab-extractor-agent-prompt.md` — Original agent prompt (archival)

## Lemmatization Must Work

```
당황했다 -> 당황하다
망설였지만 -> 망설이다
느껴졌다 -> 느끼다
돌려받아야 -> 돌려받다
살해당했어요 -> 살해당하다
해지겠다네요 -> 해지하다
```

## Non-Goals

No auth, accounts, payments, spaced repetition, mobile app, cloud sync, grammar tutor, or full dictionary app.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
