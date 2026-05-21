# tests/

## Responsibility
Test suite for the Korean vocabulary extraction pipeline and local study subsystem. Covers sentence splitting, lemmatization, candidate filtering, lemma merging, ranking, degraded mode, environment loading, translation opt-out, extraction API behavior, study DB/API behavior, privacy, and response contracts.

## Design
- **pytest**: Test framework with class-based organization.
- **Fixture Pattern**: `conftest.py` adds `backend/` to `sys.path` so tests can import backend modules directly.
- **Autouse Fixtures**: `TestLemmatization`, `TestCandidateFiltering`, `TestLemmaMerging`, and `TestRanking` use `@pytest.fixture(autouse=True)` to create `ExtractionPipeline` instance per test class.
- **Environment Isolation**: `TestDegradedMode` and `TestEnvLoading` isolate `KRDICT_API_KEY` and `.env` paths to verify degraded-mode and backend env-file behavior.
- **FastAPI TestClient**: `TestAPIEndpoint` uses `fastapi.testclient.TestClient` for HTTP-level testing.
- **Study Data Isolation**: `test_study.py` isolates app-data paths with temporary directories and reloads study modules so SQLite state does not leak between tests.

## Test Classes
| Class | Coverage | Tests |
|-------|----------|-------|
| `TestSentenceSplitting` | `split_sentences()` | Single sentence, multiple sentences, question marks, empty input, whitespace |
| `TestLemmatization` | Full pipeline lemmatization | 당황했다→당황하다, 망설였지만→망설이다, 느껴졌다→느끼다, 돌려받아야→돌려받다, 살해당했어요→살해당하다, 해지겠다네요→해지다 |
| `TestCandidateFiltering` | Particle/ending filtering | Particles removed, content words kept, endings removed |
| `TestLemmaMerging` | Duplicate lemma merging | Merging, frequency counting |
| `TestRanking` | Ranking algorithm | Frequency ranking, word count limit, empty candidates |
| `TestEmptyInput` | Input validation | Empty text raises ValueError, whitespace raises ValueError |
| `TestDegradedMode` | No API key behavior | No crash without key, extraction works without key |
| `TestEnvLoading` | `.env` loading | Backend `.env` is loaded without overriding existing environment |
| `TestAPIEndpoint` | HTTP endpoint | Empty text returns error, valid request returns 200, word count respected, sentence translation can be disabled |

## Study Tests
| File | Coverage | Tests |
|------|----------|-------|
| `test_study.py` | Local SQLite study subsystem | Schema init and no raw extraction text persistence; save/list/review flow with full fields and duplicate-save SRS preservation; known/ignored filtering for due reviews and stats; dictionary config camelCase aliases |

## Running
```bash
pytest tests/ -v
```

## Integration
- Depends on: `backend/` (all modules via `sys.path` injection)
