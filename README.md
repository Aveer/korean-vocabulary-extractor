# Korean Vocab Extractor

Paste Korean text → get study-ready vocabulary cards filtered by TOPIK II level.

## Overview

Korean Vocab Extractor is a vocabulary extraction study app for Korean learners. It takes Korean text as input, uses morphological analysis to lemmatize words, ranks them by difficulty and relevance, and produces study cards with English glosses, source sentences, and export options (plain text, CSV, Anki CSV).

**Key features:**
- Morphology-aware lemmatization via `kiwipiepy` (Kiwi)
- TOPIK II level filtering (`TOPIK_II_3` through `TOPIK_II_6`, plus `ANY`)
- Dictionary lookup from the National Institute of Korean Language (NIKL) API
- Deterministic ranking based on frequency, POS, level match, and source context
- Local dictionary cache (JSON) to minimize API calls
- Degraded mode — works without an API key (glosses will be empty)
- Export: copy all, standard CSV, Anki-compatible CSV

**Non-goals:** authentication, accounts, spaced repetition, mobile app, cloud sync, grammar tutoring, or a full dictionary app.

## Prerequisites

- **Python 3.12+** (backend)
- **Node.js 18+** and npm (frontend)

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and optionally add your NIKL API key:

```bash
cp ../.env.example .env
# Edit .env and set KRDICT_API_KEY
```

The app works without an API key, but English glosses will be empty.

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

## Environment Variables

| Variable           | Required | Description                                              |
| ------------------ | -------- | -------------------------------------------------------- |
| `KRDICT_API_KEY`   | No       | NIKL dictionary API key. Leave empty for degraded mode.  |

Get a key at: https://www.korean.go.kr/portal/outer/main.do

## Usage

1. Paste Korean text into the textarea
2. Select your target TOPIK II level (`ANY`, `TOPIK_II_3`–`TOPIK_II_6`)
3. Set the desired number of vocabulary words
4. Click **Extract Vocabulary**
5. Review the results and use **Copy All**, **Export CSV**, or **Export Anki CSV**

## API

### `POST /api/extract-vocab`

Extract vocabulary from Korean text.

**Request body:**
```json
{
  "text": "한국어 학습을 시작했습니다.",
  "wordCount": 10,
  "targetLevel": "TOPIK_II_4",
  "includeSentenceTranslation": true
}
```

| Field                        | Type    | Required | Description                                                  |
| ---------------------------- | ------- | -------- | ------------------------------------------------------------ |
| `text`                       | string  | Yes      | Korean text to extract vocabulary from (max 100,000 chars).  |
| `targetLevel`                | string  | No       | TOPIK level filter. One of: `ANY`, `TOPIK_II_3`, `TOPIK_II_4`, `TOPIK_II_5`, `TOPIK_II_6`. Default: `ANY`. |
| `wordCount`                  | number  | No       | Max number of words to return (1–100, default: 20).          |
| `includeSentenceTranslation` | boolean | No       | Include English translation of source sentences. Default: `true`. |

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
      "sourceSentenceTranslation": null,
      "level": "TOPIK_II_3",
      "frequencyInText": 1,
      "reason": "Verb. Useful for comprehension."
    }
  ],
  "meta": {
    "inputLength": 18,
    "candidateCount": 5,
    "returnedCount": 1,
    "dictionaryProvider": "NIKL"
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
| `sourceSentenceTranslation` | string?  | English translation of the source sentence (currently always null). |
| `level`                     | string?  | Assigned TOPIK level: `TOPIK_I_1`–`TOPIK_I_2`, `TOPIK_II_3`–`TOPIK_II_6`, `unknown`, or null. |
| `frequencyInText`           | number   | Number of times this lemma appears in the input text (≥1).        |
| `reason`                    | string   | Human-readable explanation of why this word was selected.         |

### ExtractMeta fields

| Field                  | Type   | Description                                          |
| ---------------------- | ------ | ---------------------------------------------------- |
| `inputLength`          | number | Length of input text in characters.                   |
| `candidateCount`       | number | Total unique lemmas before ranking.                   |
| `returnedCount`        | number | Number of cards returned after ranking.               |
| `dictionaryProvider`   | string | `"NIKL"` if API key available, `"none"` otherwise.   |

## Extraction Pipeline

The backend runs a 9-stage pipeline:

1. **Normalize input** — clean whitespace and invalid characters
2. **Sentence split** — split on Korean punctuation (`.`, `?`, `!`, `…`, `다.`, `요.`, `죠.`)
3. **Morphological analysis** — tokenize with Kiwi (`kiwipiepy`), extracting surface form, lemma, and POS for each token
4. **Candidate filtering** — keep nouns, verbs, adjectives, adverbs; drop particles, endings, punctuation, numbers, auxiliaries
5. **Lemmatization** — reduce inflected forms to dictionary form (e.g., `당황했다` → `당황하다`)
6. **Duplicate merging** — merge tokens sharing the same lemma, tracking frequency and source sentences
7. **Dictionary lookup** — fetch English glosses from NIKL API (cached in JSON)
8. **TOPIK level matching** — assign TOPIK II level based on word difficulty
9. **Ranking & formatting** — score candidates by frequency, POS, level match, and source quality; return top N

## Limitations

- **Dictionary coverage:** NIKL API may not have entries for all words, especially slang, neologisms, or specialized terms
- **No sentence translation:** The app does not use an LLM or translation API for sentence-level translation by default
- **Offline-only cache:** Dictionary cache is stored as a local JSON file; it does not persist across deployments unless the file is preserved
- **No user accounts or progress tracking:** Each extraction is independent; there is no spaced repetition or learning history
- **Single-language:** Only Korean-to-English extraction is supported

## Testing

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

The test suite covers sentence splitting, lemmatization, candidate filtering, lemma merging, ranking, empty input handling, degraded mode, and API endpoint behavior.

## License

MIT
