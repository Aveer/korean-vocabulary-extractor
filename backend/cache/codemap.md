# backend/cache/

## Responsibility
Persistent dictionary cache using JSON file storage. Reduces API calls to the NIKL dictionary by caching lookup results keyed by lemma.

## Design
- **JSON File Backend**: `DictCache` class reads/writes a single JSON file (`cache_data/dictionary_cache.json`).
- **LRU-like Eviction**: When cache exceeds `MAX_CACHE_SIZE` (10,000 entries), evicts the 20% least-recently-used entries based on `last_used_at` timestamp.
- **Fault-Tolerant**: `_load()` and `_save()` wrap I/O in try/except — cache failures are silent (cache is optional).
- **Factory Pattern**: `create_cache()` returns a `DictCache` instance with default path.

## Flow
1. `create_cache()` → `DictCache("backend/cache_data/dictionary_cache.json")`
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
