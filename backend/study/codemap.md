# backend/study/

## Responsibility
Local-first study persistence for the sentence-mining loop. Stores explicit user-saved vocabulary cards, lemma known/ignored status, SRS review state, review logs, XP, streak, and level stats in SQLite.

## Design
- **SQLite database**: `study.sqlite3` lives under `get_data_dir()` from `backend/config_paths.py`; `KVE_DATA_DIR` can override the app-data directory for tests and packaged smoke runs.
- **Privacy boundary**: Extraction does not persist raw pasted passages. Only explicit saved-card fields such as `sourceFragment`, `sourceSentence`, glosses, translations, and generated study/export lines are stored.
- **Migration-safe init**: `db.init_db()` creates tables and adds missing columns through idempotent `ALTER TABLE` checks.
- **Service boundary**: `service.py` owns validation, idempotent saves, known/ignored status, due review scheduling, and stats derivation.

## Files
| File | Responsibility |
| ---- | -------------- |
| `__init__.py` | Package marker for study subsystem imports and PyInstaller collection. |
| `db.py` | Database path resolution, connection setup, schema initialization, migration helpers, JSON parsing. |
| `service.py` | Card save/list/delete, lemma status, due reviews, review scheduling, XP/streak/stats. |

## Schema
- `schema_meta` — schema metadata/version marker.
- `lemmas` — one row per normalized lemma with status `new`, `known`, or `ignored`.
- `cards` — saved study cards keyed by id, unique on `(lemma, source_fragment)`, with SRS fields (`due_at`, `interval_days`, `ease`, `repetitions`, `lapses`).
- `reviews` — append-only review log containing rating, interval/ease after review, XP gained, and timestamp.

## Flow
1. `api/study.py` receives a study request and calls `study.service`.
2. `service.save_card()` upserts lemma metadata and card fields while preserving existing SRS progress on duplicate saves.
3. `service.set_lemma_status()` marks lemmas known/ignored/new; known/ignored lemmas are excluded from due reviews and default extraction results.
4. `service.due_reviews()` returns due unsuspended cards whose lemmas are not known/ignored.
5. `service.review_card()` applies a simple SRS schedule and records XP in `reviews`.
6. `service.stats()` derives today review count, due count, deck size, known/ignored counts, XP, level, and current streak.

## Integration
- Consumed by: `api/study.py`, `api/extract_vocab.py`.
- Depends on: `backend/config_paths.py`, stdlib `sqlite3`, `json`, `math`, `uuid`, `datetime`.
- Tested by: `tests/test_study.py`.
