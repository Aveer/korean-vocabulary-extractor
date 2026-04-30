# frontend/src/

## Responsibility
Frontend application source code. Contains the React application entry point, main component, styles, type definitions, and UI components.

## Design
- **Single-Page Architecture**: `main.tsx` bootstraps React → `App.tsx` is the root component managing all state.
- **State Management**: Local `useState` hooks — no external state library.
- **API Communication**: `fetch()` calls to `/api/extract-vocab` with JSON request/response.
- **Type-Driven**: TypeScript interfaces in `types/` define the contract between frontend and backend.

## Files
| File | Responsibility |
|------|----------------|
| `main.tsx` | React entry point: `ReactDOM.createRoot` → `<React.StrictMode><App /></React.StrictMode>` |
| `App.tsx` | Main app: text input, TOPIK level selector, word count, extract button, results display |
| `App.css` | App-specific styles: layout, header, input section, results, cards, badges |
| `index.css` | Global styles: reset, typography, colors, responsive base |
| `types/` | TypeScript interfaces: `ExtractVocabRequest`, `VocabCard`, `ExtractMeta`, `ExtractVocabResponse` |
| `components/` | Reusable UI components: `VocabCard`, `ExportActions` |

## State Flow
1. User pastes Korean text → `setText()`
2. User selects TOPIK level → `setTargetLevel()`
3. User adjusts word count → `setWordCount()`
4. User clicks "Extract" → `handleExtract()` → `POST /api/extract-vocab`
5. Response → `setCards(data.cards)` → renders `VocabCard` list + `ExportActions`

## Integration
- Consumed by: `main.tsx` (imports `App`)
- Depends on: `components/`, `types/`
