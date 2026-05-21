# frontend/src/

## Responsibility
Frontend application source code. Contains the React application entry point, main study-game component, styles, type definitions, and UI components.

## Design
- **Single-Page Architecture**: `main.tsx` bootstraps React → `App.tsx` is the root component managing Extract / Deck / Review / Progress tabs.
- **State Management**: Local `useState` hooks — no external state library.
- **API Communication**: `fetch()` calls to `/api/extract-vocab`, `/api/dictionary-config`, and `/api/study/*` with JSON request/response.
- **Type-Driven**: TypeScript interfaces in `types/` define the contract between frontend and backend.

## Files
| File | Responsibility |
|------|----------------|
| `main.tsx` | React entry point: `ReactDOM.createRoot` → `<React.StrictMode><App /></React.StrictMode>` |
| `App.tsx` | Main app: quest setup, extraction, study API calls, deck view, review flow, progress view |
| `App.css` | App-specific styles: gamified layout, tabs, panels, results, cards, review/progress states |
| `index.css` | Global styles: reset, typography, light/dark theme CSS variables, responsive base |
| `types/` | TypeScript interfaces: extraction, dictionary config, study cards, due reviews, stats |
| `components/` | Reusable UI components: `VocabCard`, `ExportActions`, `ReadingHighlights` |

## State Flow
1. User pastes Korean text → `setText()`
2. User selects TOPIK level/quest size and known/ignored filters
3. User clicks "Start quest" → `handleExtract()` → `POST /api/extract-vocab`
4. Response → `setCards(data.cards)` → renders `ReadingHighlights`, `VocabCard` list, save/status actions, and `ExportActions`
5. Study actions call `/api/study/cards`, `/api/study/lemmas/{lemma}/status`, `/api/study/reviews/*`, and `/api/study/stats`

## Integration
- Consumed by: `main.tsx` (imports `App`)
- Depends on: `components/`, `types/`
