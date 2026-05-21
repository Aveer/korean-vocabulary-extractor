import { VocabCard } from "../types";

interface Props {
  cards: VocabCard[];
}

export default function ExportActions({ cards }: Props) {
  const copyAll = () => {
    // Copy compact study lines, one per line
    const text = cards
      .map((card) => card.studyLine)
      .join("\n");

    navigator.clipboard.writeText(text).catch(() => {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    });
  };

  const exportCSV = () => {
    // Two-column CSV: front,back
    const header = "front,back";
    const rows = cards.map((card) => {
      const escape = (s: string) => `"${s.replace(/"/g, '""')}"`;
      return [escape(card.csvFront), escape(card.csvBack)].join(",");
    });
    downloadFile([header, ...rows].join("\n"), "vocab.csv", "text/csv");
  };

  const exportAnkiCSV = () => {
    // Anki CSV: Front,Back,Example,Level
    const header = "Front,Back,Example,Level";
    const rows = cards.map((card) => {
      const escape = (s: string) => `"${s.replace(/"/g, '""')}"`;
      const front = escape(card.lemma);
      const gloss = card.englishGlosses.join("; ");
      const example = card.sourceFragmentTranslation
        ? `${card.sourceFragment}\n${card.sourceFragmentTranslation}`
        : card.sourceFragment;
      const back = escape(`${gloss}\n\n${example}`);
      const level = escape(card.level || "unknown");
      return [front, back, escape(example), level].join(",");
    });
    downloadFile([header, ...rows].join("\n"), "vocab_anki.csv", "text/csv");
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="export-actions">
      <button className="export-btn" onClick={copyAll}>
        Copy quest lines
      </button>
      <button className="export-btn" onClick={exportCSV}>
        Export CSV
      </button>
      <button className="export-btn" onClick={exportAnkiCSV}>
        Export Anki CSV
      </button>
    </div>
  );
}
