# tests/

## Responsibility
Test suite for the Korean vocabulary extraction pipeline. Covers sentence splitting, lemmatization, candidate filtering, lemma merging, ranking, degraded mode, and API endpoint behavior.

## Design
- **pytest**: Test framework with class-based organization.
- **Fixture Pattern**: `conftest.py` adds `backend/` to `sys.path` so tests can import backend modules directly.
- **Autouse Fixtures**: `TestLemmatization`, `TestCandidateFiltering`, `TestLemmaMerging`, and `TestRanking` use `@pytest.fixture(autouse=True)` to create `ExtractionPipeline` instance per test class.
- **Environment Isolation**: `TestDegradedMode` tests pop/restore `KRDICT_API_KEY` to verify degraded-mode behavior.
- **FastAPI TestClient**: `TestAPIEndpoint` uses `fastapi.testclient.TestClient` for HTTP-level testing.

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
| `TestAPIEndpoint` | HTTP endpoint | Empty text returns error, valid request returns 200, word count respected |

## Running
```bash
pytest tests/ -v
```

## Integration
- Depends on: `backend/` (all modules via `sys.path` injection)
