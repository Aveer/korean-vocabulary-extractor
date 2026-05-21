# backend/dictionary/ AGENTS.md

## Provider Singleton Must Be Reset on Config Change
`extract_vocab.py` caches `_provider` as a module-level singleton. Changing dictionary config (PUT `/api/dictionary-config`) MUST set `_provider = None` or the old provider stays active until server restart.

## Dictionary Config File
Settings are stored at `get_config_path()` from `backend/config_paths.py` (OS app data such as `%APPDATA%/KoreanVocabExtractor/dictionary_config.json` on Windows, with project-relative fallback for unusual development environments). The file contains `provider` ("bundled" or "nikl") and `api_key`. Created lazily on first PUT.

## Bundled Dictionary
`bundled_dict.json` (5.1 MB, 67K entries) from kengdic (MPL 2.0 / LGPL 2.0+). Rebuild with `scripts/build_bundled_dict.py`. kengdic TSV is `kengdic.tsv` (not `kengdic_2011.tsv`) and level column is A/B/C/D (not TOPIK).

Packaged builds must include `backend/dictionary/bundled_dict.json`; the PyInstaller spec places it under `backend/dictionary/` inside the bundle so `BundledProvider` can find it in frozen apps.

`GET /api/dictionary-config` responds with frontend-facing camelCase aliases (`apiKeySet`, `bundledAvailable`, `bundledEntryCount`, `bundledSource`). Do not return the raw API key.

## Provider Switching
`create_provider()` reads config file first, then falls back to env var. `KRDICT_API_KEY` env var still works but config file takes precedence.
