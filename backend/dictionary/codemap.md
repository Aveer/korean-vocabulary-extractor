# backend/dictionary/

## Responsibility
Dictionary lookup abstraction layer. Provides Korean-English dictionary definitions, glosses, and TOPIK levels via a pluggable provider interface with degraded-mode support.

## Design
- **Abstract Base Class**: `DictionaryProvider` defines the interface (`lookup()`, `is_available()`).
- **Factory Pattern**: `create_provider()` checks `KRDICT_API_KEY` env var — returns `NIKLProvider` if key exists, `NullProvider` otherwise.
- **Null Object Pattern**: `NullProvider` implements the interface with empty returns, enabling degraded mode without conditional logic in callers.
- **Rate Limiting**: `NIKLProvider` enforces 0.5s minimum interval between API requests.
- **Caching**: `NIKLProvider` wraps all lookups through `cache.store.DictCache`.

## Flow
1. `create_provider()` → checks `KRDICT_API_KEY` → returns `NIKLProvider` or `NullProvider`
2. `provider.lookup(lemma)`:
   - Check cache first → return cached result on hit
   - Rate limit → make HTTP GET to NIKL API
   - Parse JSON response → extract glosses, definition, TOPIK level
   - Cache result → return tuple
3. `_parse_response()` handles NIKL's nested JSON structure (`channel.item[].trans[].en[]`, `kr[]`, `topik.level`)
4. `_map_topik_level()` maps NIKL level strings ("1"-"6") to `TOPIK_I_1` / `TOPIK_II_3` etc.

## Integration
- Consumed by: `api/extract_vocab.py` (via `create_provider()`)
- Depends on: `cache/store.py`, `httpx`
