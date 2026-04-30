# frontend/src/types/

## Responsibility
TypeScript type definitions for the frontend-backend API contract. Mirrors the backend Pydantic models to ensure type safety across the full stack.

## Types

### Enums
- `TargetLevel`: `"ANY" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6"`
- `Pos`: `"noun" | "verb" | "adjective" | "adverb" | "phrase" | "unknown"`
- `VocabLevel`: `"TOPIK_I_1" | "TOPIK_I_2" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6" | "unknown"`

### Interfaces
- `ExtractVocabRequest`: text, targetLevel, wordCount, includeSentenceTranslation
- `VocabCard`: lemma, display, pos, englishGlosses, koreanDefinition?, sourceSentence, sourceSentenceTranslation?, level?, frequencyInText, reason
- `ExtractMeta`: inputLength, candidateCount, returnedCount, dictionaryProvider
- `ExtractVocabResponse`: cards[], meta

## Design
- **CamelCase Properties**: Matches JSON alias convention from backend Pydantic models (`alias="targetLevel"`).
- **Optional Fields**: `?` suffix for nullable/optional fields (`koreanDefinition?`, `sourceSentenceTranslation?`, `level?`).
- **Single Barrel Export**: `index.ts` exports all types from one location.

## Integration
- Consumed by: `App.tsx`, `components/VocabCard.tsx`, `components/ExportActions.tsx`
- Depends on: None (pure type definitions)
