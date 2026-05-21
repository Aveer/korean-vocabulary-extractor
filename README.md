# Korean Vocab Extractor

Paste Korean text → turn it into a local study quest with vocabulary cards, review, and progress.

## Overview

Korean Vocab Extractor is a vocabulary extraction and sentence-mining study app for Korean learners. It takes Korean text as input, uses morphological analysis to lemmatize words, ranks them by difficulty and relevance, and produces study cards with English glosses, source sentences, local review, and export options (plain text, CSV, Anki CSV).

**Key features:**
- Morphology-aware lemmatization via `kiwipiepy` (Kiwi)
- TOPIK II level filtering (`TOPIK_II_3` through `TOPIK_II_6`, plus `ANY`)
- Offline bundled Korean-English dictionary (67K entries) with optional NIKL API provider
- Optional sentence-level English translation via Google Translate (`deep-translator`)
- Deterministic ranking based on frequency, POS, level match, and source context
- Local dictionary config/cache stored in a user-writable app data directory
- Local study deck stored in SQLite under app data: save cards, mark known/ignored, and review due cards
- Lightweight gamification: XP, streak, level progress, and daily quest-style progress view
- Degraded/offline mode — works without an API key by using the bundled dictionary
- Export: copy quest lines, standard CSV, Anki-compatible CSV

**Non-goals:** authentication, accounts, mobile app, cloud sync, grammar tutoring, or a full dictionary app.

## Prerequisites

- **Python 3.12+** (backend)
- **Node.js 20+** and npm (frontend)
- **Windows** only if you need to build the `.exe` locally (PyInstaller does not cross-compile Windows executables)

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `backend/.env` and optionally add your NIKL API key:

```bash
cp ../.env.example .env
# Edit .env and set KRDICT_API_KEY
```

The backend also reads a root `.env` as a fallback. The app works without an
API key by using the bundled offline dictionary; set `KRDICT_API_KEY` only if
you want to use the NIKL provider.

### Frontend

```bash
cd frontend
npm install
```

## Running

### Development

**Backend** (in one terminal):
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Frontend** (in another terminal):
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser. The frontend proxies API requests to the backend at `http://localhost:8000`.

### Production

```bash
cd frontend
npm run build   # outputs to frontend/dist/

cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Serve `frontend/dist/` with any static file server, configuring the API base URL to your backend.

### Packaged desktop executable

The packaged app starts the FastAPI backend, serves the built frontend, and
opens the local app in your default browser. The build script also smoke-tests
the packaged executable by checking `/api/health`, loading the frontend HTML,
verifying bundled dictionary availability, running a small extraction request
with sentence translation disabled, and exercising the local study APIs.

**Windows `.exe` build:**

```powershell
# From the project root on Windows
.\scripts\build-windows.ps1 -Clean
```

Output:

```text
dist\KoreanVocabExtractor\KoreanVocabExtractor.exe
dist\KoreanVocabExtractor.zip
```

**Cross-platform local package build:**

```bash
# From the project root, using the Python environment that has build access
python scripts/build_package.py --clean
```

On Linux/macOS this produces a platform-native `dist/KoreanVocabExtractor/KoreanVocabExtractor`
binary rather than a Windows `.exe`. To build a Windows `.exe`, run on Windows or
use the **Build Windows Portable** GitHub Actions workflow.

GitHub Actions artifacts are intended for non-developer Windows users: download
the `KoreanVocabExtractor-Windows-*` artifact, extract it once, open the
`KoreanVocabExtractor` folder, and double-click `KoreanVocabExtractor.exe`. No
Python, Node.js, or repository checkout is required.

Run the packaged app:

```powershell
dist\KoreanVocabExtractor\KoreanVocabExtractor.exe

# Useful for smoke tests/CI:
dist\KoreanVocabExtractor\KoreanVocabExtractor.exe --no-browser --port 8765
```

The executable stores dictionary settings, dictionary cache, and local study
data under the OS app data directory (`%APPDATA%\KoreanVocabExtractor` on
Windows, XDG data directory on Linux, and
`~/Library/Application Support/KoreanVocabExtractor` on macOS).

## Environment Variables

| Variable           | Required | Description                                              |
| ------------------ | -------- | -------------------------------------------------------- |
| `KRDICT_API_KEY`   | No       | NIKL dictionary API key. Leave empty to use the bundled offline dictionary. |

Get a key at: https://www.korean.go.kr/portal/outer/main.do

## Usage

1. Paste Korean text into the Extract tab.
2. Select your target TOPIK II level (`ANY`, `TOPIK_II_3`–`TOPIK_II_6`) and quest size.
3. Choose whether to skip known/ignored lemmas, then click **Start quest**.
4. Save useful cards to the local deck, mark obvious words known, or ignore noise.
5. Review due cards in the Review tab and track XP/streak/level progress in Progress.
6. Use **Copy quest lines**, **Export CSV**, or **Export Anki CSV** when you want external study files.

## API

### `POST /api/extract-vocab`

Extract vocabulary from Korean text.

**Request body:**
```json
{
  "text": "한국어 학습을 시작했습니다.",
  "wordCount": 10,
  "targetLevel": "TOPIK_II_4",
  "includeSentenceTranslation": true,
  "excludeKnown": true,
  "excludeIgnored": true
}
```

| Field                        | Type    | Required | Description                                                  |
| ---------------------------- | ------- | -------- | ------------------------------------------------------------ |
| `text`                       | string  | Yes      | Korean text to extract vocabulary from (max 100,000 chars).  |
| `targetLevel`                | string  | No       | TOPIK level filter. One of: `ANY`, `TOPIK_II_3`, `TOPIK_II_4`, `TOPIK_II_5`, `TOPIK_II_6`. Default: `ANY`. |
| `wordCount`                  | number  | No       | Max number of words to return (1–100, default: 20).          |
| `includeSentenceTranslation` | boolean | No       | Include English translation of source sentences. Default: `true`. |
| `excludeKnown`               | boolean | No       | Exclude lemmas marked known in the local study DB. Default: `true`. |
| `excludeIgnored`             | boolean | No       | Exclude lemmas marked ignored in the local study DB. Default: `true`. |

**Response:**
```json
{
  "cards": [
    {
      "lemma": "시작하다",
      "display": "시작하다",
      "pos": "verb",
      "englishGlosses": ["to start", "to begin"],
      "koreanDefinition": null,
      "sourceSentence": "한국어 학습을 시작했습니다.",
      "sourceSentenceTranslation": "I started learning Korean.",
      "sourceFragment": "시작했습니다.",
      "studyLine": "(to start, to begin) 한국어 학습을 시작했습니다. (시작하다) = I started learning Korean.",
      "csvFront": "(to start, to begin) 한국어 학습을 시작했습니다. (시작하다)",
      "csvBack": "I started learning Korean.",
      "level": "TOPIK_II_3",
      "frequencyInText": 1,
      "difficultyScore": 3.0,
      "reason": "Verb. Useful for comprehension.",
      "studyStatus": "new",
      "savedCardId": null
    }
  ],
  "meta": {
    "inputLength": 18,
    "candidateCount": 5,
    "returnedCount": 1,
    "dictionaryProvider": "bundled"
  }
}
```

### VocabCard fields

| Field                       | Type     | Description                                                      |
| --------------------------- | -------- | ---------------------------------------------------------------- |
| `lemma`                     | string   | Dictionary form of the word (e.g., `시작하다`).                   |
| `display`                   | string   | Display form for the card (usually same as lemma).                |
| `pos`                       | string   | Simplified POS: `noun`, `verb`, `adjective`, `adverb`, `phrase`, `unknown`. |
| `englishGlosses`            | string[] | English translations from dictionary lookup.                      |
| `koreanDefinition`          | string?  | Korean definition from dictionary (may be null).                  |
| `sourceSentence`            | string   | Sentence from the input text containing the word.                 |
| `sourceSentenceTranslation` | string?  | English translation of the source sentence via Google Translate. |
| `sourceFragment`            | string   | Shortest useful Korean fragment containing the word.              |
| `studyLine`                 | string   | Pre-formatted study line: `(glosses) sentence. (lemma) = translation`. |
| `csvFront`                  | string   | CSV front column: `(glosses) sentence. (lemma)`.                  |
| `csvBack`                   | string   | CSV back column: English translation of the sentence.             |
| `level`                     | string?  | Assigned TOPIK level: `TOPIK_I_1`–`TOPIK_I_2`, `TOPIK_II_3`–`TOPIK_II_6`, `unknown`, or null. |
| `frequencyInText`           | number   | Number of times this lemma appears in the input text (≥1).        |
| `difficultyScore`           | number   | Difficulty score 1-6 (1-2 beginner, 3-4 intermediate, 5-6 advanced). |
| `reason`                    | string   | Human-readable explanation of why this word was selected.         |
| `studyStatus`               | string?  | Local lemma status: `new`, `known`, or `ignored`.                  |
| `savedCardId`               | string?  | Local deck card id if this lemma/fragment is already saved.        |

### Study API

The local study API persists only explicit study actions in `study.sqlite3`
under the app data directory. Extraction itself does not save raw pasted text.

| Endpoint | Description |
| -------- | ----------- |
| `POST /api/study/cards` | Save or update a study card from an extracted `VocabCard`-like payload. Duplicate lemma+fragment saves are idempotent and preserve SRS progress. |
| `GET /api/study/cards?limit=100&offset=0` | List saved local deck cards plus total count. |
| `DELETE /api/study/cards/{card_id}` | Remove a saved card. |
| `PUT /api/study/lemmas/{lemma}/status` | Mark a lemma `new`, `known`, or `ignored`; known/ignored lemmas are skipped by default in extraction and review. |
| `GET /api/study/reviews/due?limit=20` | Return due review cards and total due count. |
| `POST /api/study/reviews/{card_id}` | Submit review rating `again`, `hard`, `good`, or `easy`; updates due date/ease/repetitions and returns XP gained. |
| `GET /api/study/stats` | Return today reviews, due count, total cards, known/ignored counts, streak, XP, and level. |

### ExtractMeta fields

| Field                            | Type   | Description                                                          |
| -------------------------------- | ------ | -------------------------------------------------------------------- |
| `inputLength`                    | number | Length of input text in characters.                                   |
| `candidateCount`                 | number | Total unique lemmas before ranking.                                   |
| `returnedCount`                  | number | Number of cards returned after ranking.                               |
| `dictionaryProvider`             | string | `"bundled"` for offline dictionary, `"nikl"` for NIKL API.           |
| `selectedTargetLevel`            | string? | Target TOPIK level selected by user.                                  |
| `candidateCountBeforeFiltering`  | number? | Candidates before level filtering (debug).                            |
| `levelDistribution`              | object? | Distribution of candidate levels (debug).                             |

## Extraction Pipeline

The backend runs a 9-stage pipeline:

1. **Normalize input** — clean whitespace and invalid characters
2. **Sentence split** — split on Korean punctuation (`.`, `?`, `!`, `…`, `다.`, `요.`, `죠.`)
3. **Morphological analysis** — tokenize with Kiwi (`kiwipiepy`), extracting surface form, lemma, and POS for each token
4. **Candidate filtering** — keep nouns, verbs, adjectives, adverbs; drop particles, endings, punctuation, numbers, auxiliaries
5. **Lemmatization** — reduce inflected forms to dictionary form (e.g., `당황했다` → `당황하다`)
6. **Duplicate merging** — merge tokens sharing the same lemma, tracking frequency and source sentences
7. **Dictionary lookup** — fetch English glosses from the bundled dictionary or optional NIKL API (cached in JSON)
8. **TOPIK level matching** — assign TOPIK II level based on word difficulty
9. **Ranking & formatting** — score candidates by frequency, POS, level match, and source quality; optionally filter known/ignored lemmas and annotate saved-card status before returning top N

## Limitations

- **Dictionary coverage:** The bundled dictionary and NIKL API may not have entries for all words, especially slang, neologisms, or specialized terms
- **Sentence translation:** Uses Google Translate via `deep-translator` for sentence-level English translations. Requires internet connection; translations may be empty if the service is unavailable.
- **Local-only data:** Dictionary cache, settings, and study progress are stored on the current device only; there is no account or cloud sync
- **Simple SRS:** Review scheduling is intentionally lightweight and local-first, not a full FSRS/Anki replacement
- **Single-language:** Only Korean-to-English extraction is supported

## Testing

```bash
backend/venv/bin/python -m pytest tests/ -v
npm run build --prefix frontend
```

The test suite covers sentence splitting, lemmatization, candidate filtering,
lemma merging, ranking, empty input handling, degraded mode, environment loading,
translation opt-out, extraction API behavior, study DB/API behavior, local privacy,
and response format contracts.

## License

MIT
