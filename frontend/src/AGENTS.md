# frontend/src/ AGENTS.md

## Theme System
Theme stored in `localStorage` key `"theme"` ("light" | "dark"). Applied via `document.documentElement.dataset.theme`. CSS uses `[data-theme="dark"]` selector with CSS custom properties defined in `index.css`. All colors in `App.css` use `var(--*)` — never hardcode colors.

## Dictionary Config
Fetched from `GET /api/dictionary-config` on mount. Saved via `PUT /api/dictionary-config`. Config persists on the backend at `get_config_path()` from `backend/config_paths.py` (OS app data, with project-relative fallback). Do not expose `KRDICT_API_KEY` directly to frontend code.

## Study UI
The app has Extract / Deck / Review / Progress tabs. Study data comes from `/api/study/*` and is persisted by the backend in local SQLite app data, not browser `localStorage`. Frontend `localStorage` is only for UI preferences such as theme.

Keep study flows privacy-forward: extraction may display the current pasted passage and reading highlights, but full pasted passages are not saved unless a future explicit saved-reading feature is added. Save actions may persist individual card fields returned by the backend (`sourceFragment`, `sourceSentence`, glosses, translations).
