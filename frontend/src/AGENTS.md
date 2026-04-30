# frontend/src/ AGENTS.md

## Theme System
Theme stored in `localStorage` key `"theme"` ("light" | "dark"). Applied via `document.documentElement.dataset.theme`. CSS uses `[data-theme="dark"]` selector with 27 CSS custom properties defined in `index.css`. All colors in `App.css` use `var(--*)` — never hardcode colors.

## Dictionary Config
Fetched from `GET /api/dictionary-config` on mount. Saved via `PUT /api/dictionary-config`. Config persists on backend in `cache_data/dictionary_config.json`.
