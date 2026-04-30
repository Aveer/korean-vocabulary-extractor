# Korean Vocab Extractor — Agent Implementation Prompt

You are implementing a Korean vocabulary extractor study app.

## Goal

Build an app where the user can paste Korean text, select a target TOPIK II level, enter the number of vocabulary items to extract, and receive study-ready vocabulary cards.

The app should extract useful words from the pasted Korean passage, normalize them to dictionary forms, rank them by usefulness and level fit, and return examples from the original text.

The expected compact output format is:

```text
(English gloss) Korean source sentence. (lemma) = English sentence translation.
```

Example:

```text
(drowning) 익사입니다. (익사) = It was drowning.
```

## Important Product Notes

Use `TOPIK`, not `Topic`.

TOPIK II covers levels 3, 4, 5, and 6.

The level dropdown should include:

- Any TOPIK II level
- TOPIK II Level 3
- TOPIK II Level 4
- TOPIK II Level 5
- TOPIK II Level 6

The app is for Korean learners. Do not turn this into a general translation app, chat app, or full dictionary clone.

The hardest and most important part is extraction quality.

## Architecture

Use the existing repo stack if one exists.

If the repo has no established stack, use:

- Frontend: React + Vite + TypeScript
- Backend: Python FastAPI
- Korean NLP: `kiwipiepy`
- Dictionary: National Institute of Korean Language Korean-English Learners’ Dictionary API
- Cache: SQLite or local JSON cache

Do not use DuckDuckGo as the main dictionary source.

DuckDuckGo is not structured enough for reliable vocabulary extraction. It may only be added later as a disabled fallback/debug provider.

Do not expose dictionary API keys in the browser.

## Before Coding

First inspect the repository.

Determine:

- frontend framework
- backend framework
- package manager
- project structure
- routing conventions
- API conventions
- styling conventions
- test conventions

Reuse existing patterns wherever possible.

If no structure exists, create the smallest clean structure needed for the MVP.

## Backend API

Create this endpoint:

```text
POST /api/extract-vocab
```

Request shape:

```json
{
  "text": "Korean passage here...",
  "targetLevel": "TOPIK_II_4",
  "wordCount": 20,
  "includeSentenceTranslation": true
}
```

Allowed `targetLevel` values:

```text
ANY
TOPIK_II_3
TOPIK_II_4
TOPIK_II_5
TOPIK_II_6
```

Response shape:

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

## Backend Data Types

Use equivalent backend models.

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

## Extraction Pipeline

Implement the extraction pipeline in this order.

### 1. Normalize Input

- Trim whitespace.
- Normalize repeated whitespace.
- Preserve Korean punctuation.
- Reject empty input with a useful error.
- Add a reasonable maximum input size.

### 2. Split Sentences

Split Korean text into source sentences.

The splitter should handle common endings and punctuation:

```text
.
?
!
…
다.
요.
죠.
"
”
```

The splitter does not need to be perfect in MVP, but each vocabulary card should include a usable source sentence.

### 3. Run Korean Morphological Analysis

Use `kiwipiepy`.

Extract:

- surface form
- lemma
- POS
- sentence index
- offset if available

### 4. Keep Useful Candidates

Keep:

- common nouns
- compound nouns
- verbs
- adjectives
- adverbs
- meaningful Sino-Korean nouns
- domain-specific terms
- repeated content words
- fixed expressions if detectable

Drop:

- particles
- endings
- punctuation
- isolated numbers
- common auxiliaries
- extremely basic words unless needed
- one-off names unless clearly useful
- duplicate surface forms of the same lemma

### 5. Lemmatize

Normalize Korean forms to dictionary forms.

Examples that must work:

```text
당황했다 -> 당황하다
망설였지만 -> 망설이다
느껴졌다 -> 느끼다
돌려받아야 -> 돌려받다
살해당했어요 -> 살해당하다
해지하겠다네요 -> 해지하다
```

For verbs and adjectives, prefer dictionary `-다` form.

For nouns, keep dictionary noun form.

For fixed phrases, keep natural phrase form.

### 6. Merge Duplicates

Merge candidates by lemma.

For each lemma, collect:

- frequency
- POS
- source sentences
- best source sentence
- dictionary data if available
- level data if available

### 7. Dictionary Lookup

Create a dictionary provider interface:

```ts
interface DictionaryProvider {
  lookup(lemma: string): Promise<DictionaryEntry | null>;
}
```

Implement equivalent in the backend language.

Create:

- `CacheDictionaryProvider`
- `NiklDictionaryProvider`
- `FallbackDictionaryProvider` placeholder if useful

Use environment variable:

```text
KRDICT_API_KEY=...
```

If `KRDICT_API_KEY` is missing:

- App must still run.
- Extraction must still work.
- Cards should return lemma, POS, source sentence, and frequency.
- English glosses may be empty or unavailable.
- Do not crash.

### 8. TOPIK Level Matching

If a local TOPIK vocabulary list exists, use it.

If no reliable dataset exists, mark the level as:

```text
unknown
```

or clearly estimated.

Do not invent exact TOPIK levels.

The selected level should influence ranking, not completely filter out unknown-level words.

### 9. Ranking

Implement deterministic ranking first.

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

Ranking behavior:

- Prefer useful comprehension words.
- Prefer words near the selected TOPIK level.
- Prefer meaningful words over grammar fragments.
- Prefer dictionary-backed words.
- Prefer good standalone source sentences.
- Penalize extremely basic words.
- Penalize names unless important.
- Avoid too many related variants.

### 10. Format Cards

Each card should contain enough data for the UI and export formats.

Compact study format:

```text
(english gloss) source sentence. (lemma) = translated sentence.
```

If sentence translation is unavailable, use:

```text
(english gloss) source sentence. (lemma)
```

Do not fabricate translations with high confidence. If translation is unavailable, leave it empty or mark it unavailable.

## Frontend Requirements

Create a simple study-oriented UI.

Main screen:

- Title: `Korean Vocab Extractor`
- Subtitle: `Paste Korean text and extract study-ready vocabulary.`
- Number input label: `Number of words`
- Dropdown label: `Target level`
- Textarea placeholder: `Paste a chapter or passage of Korean text here...`
- Primary button: `Extract vocabulary`

Results:

Each result card should show:

- Korean lemma
- English glosses
- POS
- TOPIK level or `unknown`
- Korean source sentence
- English sentence translation if available
- Optional note/reason

Actions:

- `Copy all`
- `Export CSV`
- `Export Anki CSV`

Loading state:

```text
Extracting vocabulary...
```

Error examples:

```text
Please paste Korean text first.
Could not extract vocabulary from this passage.
Dictionary lookup is unavailable, but extraction still worked.
```

## Export Requirements

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

## Example Expected Extractions

From a Korean crime/drama passage, the app should be able to extract vocabulary like:

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

## Tests

Add tests for:

- empty input
- very short Korean input
- long pasted passage
- Korean sentence splitting
- particle removal
- ending removal
- verb/adjective lemmatization
- duplicate lemma merging
- repeated words ranked higher
- `wordCount` respected
- missing dictionary API key does not crash
- CSV export
- Anki CSV export

Required lemmatization test cases:

```text
당황했다 -> 당황하다
망설였지만 -> 망설이다
느껴졌다 -> 느끼다
돌려받아야 -> 돌려받다
살해당했어요 -> 살해당하다
해지하겠다네요 -> 해지하다
```

## Privacy Requirements

Do not permanently store full pasted passages.

Allowed storage:

- dictionary cache by lemma
- app settings
- temporary request processing data

Do not send pasted chapters to third-party LLM APIs unless there is an explicit optional user setting.

## Implementation Order

Follow this order:

1. Inspect repository structure.
2. Identify existing frontend/backend stack.
3. Add backend endpoint with mock response.
4. Build frontend UI.
5. Wire frontend to backend.
6. Add `kiwipiepy` extraction.
7. Add filtering.
8. Add lemmatization.
9. Add duplicate merging.
10. Add deterministic ranking.
11. Add dictionary provider interface.
12. Add NIKL provider.
13. Add dictionary cache.
14. Add copy/export actions.
15. Add tests.
16. Add README setup instructions.

## README Requirements

Update or create README with:

- What the app does
- How to install dependencies
- How to run frontend
- How to run backend
- How to configure `KRDICT_API_KEY`
- Example request
- Example response
- Known limitations
- Privacy note

## Definition of Done

The task is complete when:

- A user can paste Korean text.
- A user can choose number of words.
- A user can select TOPIK II target level.
- The app returns useful vocabulary cards.
- The app does not return particles/endings as vocabulary.
- Conjugated Korean forms are normalized.
- Each card includes a source sentence.
- Missing dictionary API key does not break the app.
- Dictionary API mode enriches cards when configured.
- Copy/export works.
- Tests cover the main extraction behavior.
- README explains setup and limitations.

## Do Not Do

Do not:

- Build authentication.
- Build accounts.
- Build payments.
- Build cloud sync.
- Build spaced repetition.
- Build a full dictionary app.
- Build a grammar tutor.
- Build a general translation app.
- Scrape random dictionary websites.
- Use DuckDuckGo as the primary dictionary provider.
- Expose API keys to the frontend.
- Store pasted full chapters permanently.
- Invent exact TOPIK levels without a reliable source.
- Overbuild before proving extraction quality.

## Final Response After Implementation

When done, report:

- Files changed
- How to run frontend
- How to run backend
- How to configure `KRDICT_API_KEY`
- Example extraction result
- Known limitations
- Tests added or not added
