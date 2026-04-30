# frontend/src/components/

## Responsibility
Reusable UI components for vocabulary card display and export functionality. Dumb/presentational components that receive data via props.

## Components

### VocabCard
- **Purpose**: Renders a single vocabulary study card.
- **Props**: `{ card: VocabCard }`
- **Display**: Lemma, POS badge, TOPIK level badge, English glosses, source sentence, translation, selection reason.
- **Conditional Rendering**: Glosses, level badge, translation, and reason are conditionally shown based on data availability.

### ExportActions
- **Purpose**: Provides three export options for vocabulary results.
- **Props**: `{ cards: VocabCard[] }`
- **Actions**:
  - `copyAll()`: Copies formatted vocab list to clipboard (with fallback for older browsers).
  - `exportCSV()`: Downloads CSV with columns: Korean, English, POS, Level, Example Korean, Example English, Notes.
  - `exportAnkiCSV()`: Downloads Anki-compatible CSV with columns: Front, Back, Example, Level.
- **Helper**: `downloadFile()` creates Blob → ObjectURL → programmatic `<a>` click → cleanup.

## Design
- **Presentational Components**: No internal state — purely driven by props.
- **Default Exports**: Both components use default exports.
- **CSV Escaping**: Proper double-quote escaping for CSV values containing commas or quotes.

## Integration
- Consumed by: `App.tsx`
- Depends on: `../types` (`VocabCard` interface)
