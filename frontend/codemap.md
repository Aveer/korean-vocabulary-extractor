# frontend/

## Responsibility
React + Vite + TypeScript frontend application. Provides the user interface for pasting Korean text, configuring extraction parameters, and viewing/exporting vocabulary results.

## Design
- **Vite SPA**: Single-page application built with Vite for fast dev server and optimized production builds.
- **React 18**: Functional components with hooks (`useState`).
- **CSS Modules**: Plain CSS files (`App.css`, `index.css`) — no CSS-in-JS or framework.
- **API Proxy**: Vite dev server proxies `/api` requests to `http://localhost:8000` (FastAPI backend).
- **Type Safety**: TypeScript interfaces mirror backend Pydantic models (`types/index.ts`).

## Structure
| Path | Responsibility |
|------|----------------|
| `src/main.tsx` | React bootstrap: `ReactDOM.createRoot` → `<App />` |
| `src/App.tsx` | Main application: state management, form UI, API calls, results rendering |
| `src/components/` | Reusable UI components (`VocabCard`, `ExportActions`) |
| `src/types/` | TypeScript interfaces for API request/response types |
| `vite.config.ts` | Vite configuration with API proxy to backend |
| `package.json` | Dependencies: React, Vite, TypeScript |

## Integration
- Consumes: Backend `POST /api/extract-vocab` endpoint
- Provides: User-facing UI for vocabulary extraction
