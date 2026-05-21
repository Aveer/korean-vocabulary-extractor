# frontend/src/types/

## Responsibility
TypeScript type definitions for the frontend-backend API contract. Mirrors backend Pydantic models for extraction, dictionary config, and local study APIs.

## Types

### Enums
- `TargetLevel`: `"ANY" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6"`
- `Pos`: `"noun" | "verb" | "adjective" | "adverb" | "phrase" | "unknown"`
- `VocabLevel`: `"TOPIK_I_1" | "TOPIK_I_2" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6" | "unknown"`
- `StudyStatus`: `"new" | "known" | "ignored"`
- `ReviewRating`: `"again" | "hard" | "good" | "easy"`

### Interfaces
- `ExtractVocabRequest`: text, targetLevel, wordCount, includeSentenceTranslation, excludeKnown?, excludeIgnored?
- `VocabCard`: lemma, display, pos, englishGlosses, koreanDefinition?, sourceSentence, sourceSentenceTranslation?, level?, frequencyInText, reason, studyStatus?, savedCardId?
- `ExtractMeta`: inputLength, candidateCount, returnedCount, dictionaryProvider
- `ExtractVocabResponse`: cards[], meta
- `DictionaryConfig`: provider, apiKeySet, bundledAvailable, bundledEntryCount, bundledSource
- `SavedStudyCard`, `StudyCardsResponse`, `DueReviewCard`, `DueReviewsResponse`, `StudyStats`

## Design
- **CamelCase Properties**: Matches JSON alias convention from backend Pydantic models (`alias="targetLevel"`).
- **Optional Fields**: `?` suffix for nullable/optional fields (`koreanDefinition?`, `sourceSentenceTranslation?`, `level?`).
- **Single Barrel Export**: `index.ts` exports all types from one location.

## Integration
- Consumed by: `App.tsx`, `components/VocabCard.tsx`, `components/ExportActions.tsx`, `components/ReadingHighlights.tsx`
- Depends on: None (pure type definitions)
