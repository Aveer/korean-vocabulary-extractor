# Korean Vocab Extractor — Implementation Plan

## 1. Goal

Build a small study app for Korean learners.

The user should be able to paste Korean text, choose how many vocabulary items they want, select a target TOPIK II level, and receive study-ready vocabulary extracted from that exact passage.

The app should produce output similar to:

```text
(drowning) 익사입니다. (익사) = It was drowning.

(autopsy, post-mortem examination) 자세한 부검 결과는 일주일쯤 뒤에 통보가 갈 겁니다. (부검) = The detailed autopsy results will be reported in about a week.
```

The main value of the app is not the UI. The main value is reliable vocabulary extraction from Korean text.

---

## 2. Product Scope

### MVP Features

The MVP should include:

- Korean text input area
- Number input for desired vocabulary count
- TOPIK level dropdown
- Extract vocabulary button
- Study-card output
- Copy all button
- CSV export
- Anki CSV export
- Basic error state
- Basic loading state

### Target User

A Korean learner who wants to paste a chapter, article, dialogue, or passage and quickly get useful words to study.

### Target Levels

Use `TOPIK`, not `Topic`.

Dropdown options:

- Any TOPIK II level
- TOPIK II Level 3
- TOPIK II Level 4
- TOPIK II Level 5
- TOPIK II Level 6

TOPIK II covers intermediate and advanced Korean, roughly levels 3–6.

---

## 3. Recommended Architecture

### Frontend

Use the existing project frontend stack if one already exists.

If starting from scratch, use:

- React
- Vite
- TypeScript
- Simple CSS or Tailwind, depending on repo conventions

Frontend responsibilities:

- Collect user input
- Call backend extraction endpoint
- Display vocabulary cards
- Provide copy/export actions

### Backend

Use Python FastAPI unless the existing repo already has a backend stack.

Backend responsibilities:

- Sentence splitting
- Korean morphological analysis
- Lemmatization
- Filtering
- Ranking
- Dictionary lookup
- Cache
- API response formatting

### Korean NLP

Use `kiwipiepy` / Kiwi for Korean morphological analysis.

Reason:

- Korean needs morphology-aware parsing.
- Surface forms are highly inflected.
- Simple regex or whitespace tokenization is not enough.
- The app must normalize forms like `망설였지만` to `망설이다`.

### Dictionary Provider

Use a provider abstraction.

Primary provider:

- National Institute of Korean Language Korean-English Learners’ Dictionary API

Fallback behavior:

- If no API key is present, extraction should still work.
- Cards should still include lemma, POS, source sentence, frequency, and level estimate if available.
- English glosses can be empty or marked unavailable.
- Do not crash if dictionary lookup is unavailable.

Do not use DuckDuckGo as the primary dictionary source.

DuckDuckGo is not structured enough for reliable vocabulary extraction. It may only be added later as a disabled fallback/debug provider.

### Cache

Use SQLite or local JSON cache for dictionary lookups.

Suggested cached fields:

```text
lemma
dictionary_payload
provider
created_at
last_used_at
```

---

## 4. User Flow

1. User opens the app.
2. User pastes Korean text.
3. User chooses target level.
4. User enters desired number of words.
5. User clicks `Extract vocabulary`.
6. App sends text to backend.
7. Backend extracts, filters, ranks, and enriches vocabulary.
8. Frontend displays study cards.
9. User copies or exports the result.

---

## 5. API Design

### Endpoint

```text
POST /api/extract-vocab
```

### Request

```json
{
  "text": "Korean passage here...",
  "targetLevel": "TOPIK_II_4",
  "wordCount": 20,
  "includeSentenceTranslation": true
}
```

### Response

```json
{
  "cards": [
    {
      "lemma": "부검",
      "display": "부검",
      "pos": "noun",
      "englishGlosses": ["autopsy", "post-mortem examination"],
      "koreanDefinition": null,
      "sourceSentence": "자세한 부검 결과는 일주일쯤 뒤에 통보가 갈 겁니다.",
      "sourceSentenceTranslation": "The detailed autopsy results will be reported in about a week.",
      "level": "TOPIK_II_5",
      "frequencyInText": 1,
      "reason": "Important formal noun used in the passage's investigation context."
    }
  ],
  "meta": {
    "inputLength": 12000,
    "candidateCount": 184,
    "returnedCount": 20,
    "dictionaryProvider": "NIKL"
  }
}
```

### TypeScript Shape

```ts
type ExtractVocabRequest = {
  text: string;
  targetLevel: "ANY" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6";
  wordCount: number;
  includeSentenceTranslation: boolean;
};

type VocabCard = {
  lemma: string;
  display: string;
  pos: "noun" | "verb" | "adjective" | "adverb" | "phrase" | "unknown";
  englishGlosses: string[];
  koreanDefinition?: string | null;
  sourceSentence: string;
  sourceSentenceTranslation?: string | null;
  level?: "TOPIK_I_1" | "TOPIK_I_2" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6" | "unknown";
  frequencyInText: number;
  reason: string;
};
```

---

## 6. Extraction Pipeline

### Step 1: Normalize Input

- Trim leading/trailing whitespace.
- Normalize repeated whitespace.
- Preserve Korean punctuation where useful.
- Reject empty input.
- Set reasonable maximum input size.

### Step 2: Sentence Splitting

Split the input into Korean sentences.

Handle common Korean punctuation:

```text
.
?
!
…
”
”
다.
요.
죠.
```

The sentence splitter does not need to be perfect for MVP, but it should preserve enough context for study cards.

### Step 3: Morphological Analysis

Run Kiwi / `kiwipiepy`.

Collect tokens with:

- surface form
- lemma
- POS
- sentence index
- character offset if available

### Step 4: Candidate Filtering

Keep useful content-bearing tokens:

- nouns
- compound nouns
- verbs
- adjectives
- adverbs
- important Sino-Korean terms
- domain-specific terms
- repeated terms
- fixed expressions if detectable

Drop:

- particles
- endings
- punctuation
- isolated numbers
- common auxiliaries
- extremely common beginner words unless requested
- character names unless useful
- one-off proper nouns unless clearly important
- duplicate surface variants of the same lemma

### Step 5: Lemmatization

Normalize Korean forms to dictionary forms.

Examples:

```text
당황했다 -> 당황하다
망설였지만 -> 망설이다
느껴졌다 -> 느끼다
돌려받아야 -> 돌려받다
살해당했어요 -> 살해당하다
해지하겠다네요 -> 해지하다
```

For verbs and adjectives, prefer dictionary `-다` form.

For nouns, preserve dictionary form.

For fixed phrases, preserve natural phrase form.

### Step 6: Dictionary Lookup

For each candidate lemma:

1. Check local cache.
2. If missing, query NIKL Korean-English Learners’ Dictionary API.
3. Cache result.
4. Attach glosses/definitions to candidate.

If dictionary lookup fails:

- Keep the candidate.
- Mark dictionary confidence lower.
- Do not crash.

### Step 7: TOPIK Level Matching

If a local TOPIK vocabulary dataset exists, use it.

If not, return `unknown` or `estimated`.

Do not invent exact levels.

Target level should influence ranking but should not hide all unknown-level words.

### Step 8: Ranking

Use deterministic ranking first.

Suggested formula:

```text
score =
  frequency_score * 2.0
  + target_level_match_score * 2.0
  + content_pos_score
  + dictionary_confidence_score
  + source_sentence_quality_score
  + narrative_importance_score
  - too_easy_penalty
  - proper_name_penalty
  - duplicate_family_penalty
```

Ranking priorities:

- Prefer vocabulary useful for comprehension.
- Prefer words near the selected TOPIK level.
- Prefer meaningful words over grammar fragments.
- Prefer source sentences that are understandable on their own.
- Prefer dictionary-backed words.
- Penalize extremely basic words.
- Penalize names unless important.
- Avoid returning many variants from the same word family.

### Step 9: Format Output

Each card should support compact copy format:

```text
(english gloss) Korean source sentence. (lemma) = English sentence translation.
```

Example:

```text
(hesitate) 나는 잠시 망설였지만 의심을 살 행동은 하지 말아야 한다고 재차 생각했다. (망설이다) = I hesitated for a moment, but again thought I should not do anything suspicious.
```

---

## 7. Frontend Requirements

### Main Screen

Include:

- App title: `Korean Vocab Extractor`
- Short subtitle: `Paste Korean text and extract study-ready vocabulary.`
- Number input: `Number of words`
- Dropdown: `Target level`
- Textarea placeholder: `Paste a chapter or passage of Korean text here...`
- Button: `Extract vocabulary`

### Results

Each result card should show:

- Korean lemma
- English gloss
- POS
- TOPIK level or `unknown`
- Korean source sentence
- English sentence translation if available
- Optional reason/note

### Actions

Add:

- `Copy all`
- `Export CSV`
- `Export Anki CSV`

### Loading State

Show a simple loading state while extracting:

```text
Extracting vocabulary...
```

### Error State

Examples:

```text
Please paste Korean text first.
Could not extract vocabulary from this passage.
Dictionary lookup is unavailable, but extraction still worked.
```

---

## 8. Export Formats

### CSV

Columns:

```text
Korean, English, POS, Level, Example Korean, Example English, Notes
```

### Anki CSV

Columns:

```text
Front, Back, Example, Level
```

Suggested Anki card:

Front:

```text
부검
```

Back:

```text
autopsy; post-mortem examination

자세한 부검 결과는 일주일쯤 뒤에 통보가 갈 겁니다.
The detailed autopsy results will be reported in about a week.
```

---

## 9. Example Vocabulary From Provided Passage

The app should be able to extract items like:

```text
(autopsy, post-mortem examination) 자세한 부검 결과는 일주일쯤 뒤에 통보가 갈 겁니다. (부검) = The detailed autopsy results will be reported in about a week.

(drowning) 익사입니다. (익사) = It was drowning.

(sleep aid, sedative) 그 약은 로잘민이라는 수면 유도제였다. (수면 유도제) = The medicine was a sleep aid called Rozalmin.

(to hesitate) 나는 잠시 망설였지만 의심을 살 행동은 하지 말아야 한다고 재차 생각했다. (망설이다) = I hesitated for a moment, but again thought I should not do anything suspicious.

(background investigation) 경찰이 몰래 내 뒷조사를 하고 있다고 생각하니 섬뜩한 기분이 들었다. (뒷조사) = Thinking that the police were secretly investigating me gave me chills.

(to terminate a contract) 이젠 계약을 해지하겠다네요. (계약을 해지하다) = Now they say they will terminate the contract.

(death insurance payout) 사망보험금을 받기 위해 보험 설계사들끼리 공유하고 있는 팁 같은 게 있을지도 모른다. (사망보험금) = There might be tips shared by insurance agents for receiving a death insurance payout.

(to protest, object, argue against) 남편이 자살한 게 아니라고 항변하는 나를 김미숙 형사가 안쓰럽게 쳐다보았다. (항변하다) = Detective Kim Misuk looked at me pityingly as I insisted that my husband had not killed himself.
```

---

## 10. Testing Plan

Add tests for:

- Empty input
- Very short Korean input
- Long pasted passage
- Korean sentence splitting
- Particle removal
- Ending removal
- Verb/adjective lemmatization
- Duplicate lemma merging
- Repeated words ranked higher
- `wordCount` respected
- Missing dictionary API key does not crash
- CSV export
- Anki CSV export

### Specific Lemmatization Tests

```text
당황했다 -> 당황하다
망설였지만 -> 망설이다
느껴졌다 -> 느끼다
돌려받아야 -> 돌려받다
살해당했어요 -> 살해당하다
해지하겠다네요 -> 해지하다
```

---

## 11. Privacy and Storage

Do not permanently store full pasted passages.

Acceptable storage:

- Dictionary cache by lemma
- App settings
- Optional local browser history only if explicitly added later

Do not send pasted chapters to third-party LLM APIs unless there is a clear optional setting.

---

## 12. Implementation Order

1. Inspect existing repository structure.
2. Confirm frontend/backend stack.
3. Create mock backend endpoint.
4. Create frontend UI.
5. Wire frontend to backend.
6. Add Kiwi / `kiwipiepy` extraction.
7. Add filtering and lemmatization.
8. Add deterministic ranking.
9. Add dictionary provider interface.
10. Add NIKL dictionary provider.
11. Add dictionary cache.
12. Add copy/export actions.
13. Add tests.
14. Add README documentation.

---

## 13. Definition of Done

The MVP is done when:

- User can paste Korean text.
- User can select TOPIK II level.
- User can choose number of words.
- App returns useful vocabulary, not particles/endings.
- Conjugated words are normalized.
- Each result includes a source sentence.
- App works without a dictionary API key in degraded mode.
- API-key mode enriches cards with dictionary data.
- User can copy results.
- User can export CSV.
- User can export Anki CSV.
- Basic tests pass.
- README explains setup and limitations.

---

## 14. Non-Goals for MVP

Do not build these yet:

- User accounts
- Authentication
- Payments
- Spaced repetition scheduler
- Mobile app
- Browser extension
- Full dictionary app
- Grammar explanation engine
- Full translation app
- Automatic chapter library
- Cloud sync
- AI chat tutor

These can be added later after the extraction quality is proven.
