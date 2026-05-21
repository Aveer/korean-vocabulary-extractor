# backend/cache/

## Responsibility
Persistent dictionary cache using JSON file storage. Reduces API calls to optional dictionary providers by caching lookup results keyed by lemma.

## Design
- **JSON File Backend**: `DictCache` class reads/writes `dictionary_cache.json` under `get_cache_file()` from `backend/config_paths.py` (OS app data, with project-relative fallback).
- **LRU-like Eviction**: When cache exceeds `MAX_CACHE_SIZE` (10,000 entries), evicts the 20% least-recently-used entries based on `last_used_at` timestamp.
- **Fault-Tolerant**: `_load()` and `_save()` wrap I/O in try/except — cache failures are silent (cache is optional).
- **Factory Pattern**: `create_cache()` returns a `DictCache` instance with default path.

## Flow
1. `create_cache()` → `DictCache(get_cache_file())`
2. `cache.get(lemma)` → returns cached dict or None; updates `last_used_at` on hit
3. `cache.set(lemma, data)` → stores entry with timestamps; evicts if over capacity; saves to disk
4. `_evict()` → sorts by `last_used_at`, removes oldest 20%

## Data Format
```json
{
  "lemma": "사과",
  "glosses": ["apple"],
  "definition": "...",
  "level": "TOPIK_I_2",
  "provider": "NIKL",
  "created_at": 1234567890.0,
  "last_used_at": 1234567891.0
}
```

## Integration
- Consumed by: `dictionary/nikl.py` (`NIKLProvider`)
- Depends on: None (stdlib only: `json`, `os`, `pathlib`, `time`)
