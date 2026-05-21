# frontend/src/components/

## Responsibility
Reusable UI components for vocabulary card display, current-reading highlights, and export functionality. Components remain mostly presentational and receive data/actions via props.

## Components

### VocabCard
- **Purpose**: Renders a single vocabulary study card.
- **Props**: `{ card: VocabCard, actions?: React.ReactNode }`
- **Display**: Lemma, POS badge, TOPIK level badge, English glosses, source sentence, translation, selection reason.
- **Conditional Rendering**: Glosses, level badge, translation, reason, and card action controls are conditionally shown based on data availability.

### ReadingHighlights
- **Purpose**: Renders the current pasted Korean passage with best-effort highlights for extracted terms.
- **Props**: `{ text: string, cards: VocabCard[] }`
- **Privacy**: Works only with the current in-memory extraction text; it does not persist full pasted passages.
- **Matching**: Uses safe terms from `display`, `lemma`, and short `sourceFragment` values; no morphology reconstruction in the frontend.

### ExportActions
- **Purpose**: Provides three export options for vocabulary results.
- **Props**: `{ cards: VocabCard[] }`
- **Actions**:
  - `copyAll()`: Copies formatted quest lines to clipboard (with fallback for older browsers).
  - `exportCSV()`: Downloads CSV with columns: Korean, English, POS, Level, Example Korean, Example English, Notes.
  - `exportAnkiCSV()`: Downloads Anki-compatible CSV with columns: Front, Back, Example, Level.
- **Helper**: `downloadFile()` creates Blob → ObjectURL → programmatic `<a>` click → cleanup.

## Design
- **Presentational Components**: Components are primarily driven by props; API/stateful study behavior lives in `App.tsx`.
- **Default Exports**: Both components use default exports.
- **CSV Escaping**: Proper double-quote escaping for CSV values containing commas or quotes.

## Integration
- Consumed by: `App.tsx`
- Depends on: `../types` (`VocabCard` interface)
