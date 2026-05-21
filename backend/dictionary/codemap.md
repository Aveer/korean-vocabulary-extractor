# backend/dictionary/

## Responsibility
Dictionary lookup abstraction layer. Provides Korean-English dictionary glosses from the bundled offline dictionary by default, with optional NIKL definitions/glosses/TOPIK levels via a pluggable provider interface.

## Design
- **Abstract Base Class**: `DictionaryProvider` defines the interface (`lookup()`, `is_available()`).
- **Bundled Default**: `BundledProvider` loads `backend/dictionary/bundled_dict.json` and works without an API key.
- **Factory Pattern**: `create_provider()` reads persisted config first, then `KRDICT_API_KEY`; returns `NIKLProvider` only when provider is `nikl` and an API key is available, otherwise `BundledProvider`.
- **Rate Limiting**: `NIKLProvider` enforces 0.5s minimum interval between API requests.
- **Caching**: `NIKLProvider` wraps all lookups through `cache.store.DictCache`.

## Flow
1. `create_provider()` → reads app-data config/env → returns `BundledProvider` or `NIKLProvider`
2. `provider.lookup(lemma)`:
   - Bundled: read local JSON entry and return glosses
   - NIKL: check cache first → rate limit → HTTP GET → parse JSON → cache result
3. `_parse_response()` handles NIKL's nested JSON structure (`channel.item[].trans[].en[]`, `kr[]`, `topik.level`)
4. `_map_topik_level()` maps NIKL level strings ("1"-"6") to `TOPIK_I_1` / `TOPIK_II_3` etc.

## Integration
- Consumed by: `api/extract_vocab.py` (via `create_provider()`)
- Depends on: `cache/store.py`, `httpx`

## API Contract Notes
- Dictionary config endpoints expose provider choice and key presence only; never return the raw `KRDICT_API_KEY`.
- Frontend-facing dictionary config responses use camelCase aliases such as `apiKeySet`, `bundledAvailable`, and `bundledEntryCount`.
