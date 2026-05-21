# frontend/

## Responsibility
React + Vite + TypeScript frontend application. Provides the user interface for Korean reading quests: extracting vocabulary, saving cards to a local deck, reviewing due cards, tracking progress, and exporting results.

## Design
- **Vite SPA**: Single-page application built with Vite for fast dev server and optimized production builds.
- **React 18**: Functional components with hooks (`useState`, `useEffect`).
- **CSS Modules**: Plain CSS files (`App.css`, `index.css`) — no CSS-in-JS or framework.
- **API Proxy**: Vite dev server proxies `/api` requests to `http://localhost:8000` (FastAPI backend).
- **Type Safety**: TypeScript interfaces mirror backend Pydantic models (`types/index.ts`).
- **Local-first Study UX**: Study state is persisted through backend SQLite APIs, while frontend `localStorage` is used only for UI preferences such as theme.

## Structure
| Path | Responsibility |
|------|----------------|
| `src/main.tsx` | React bootstrap: `ReactDOM.createRoot` → `<App />` |
| `src/App.tsx` | Main application: Extract/Deck/Review/Progress tabs, API calls, study-game state, results rendering |
| `src/components/` | Reusable UI components (`VocabCard`, `ExportActions`, `ReadingHighlights`) |
| `src/types/` | TypeScript interfaces for API request/response types |
| `vite.config.ts` | Vite configuration with API proxy to backend |
| `package.json` | Dependencies: React, Vite, TypeScript |

## Integration
- Consumes: Backend `POST /api/extract-vocab`, dictionary config endpoints, and `/api/study/*`
- Provides: User-facing UI for vocabulary extraction, local deck management, SRS review, progress stats, and exports
