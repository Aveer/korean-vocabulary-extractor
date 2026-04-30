import { VocabCard } from "../types";

interface Props {
  cards: VocabCard[];
}

export default function ExportActions({ cards }: Props) {
  const copyAll = () => {
    const text = cards
      .map((card) => {
        const gloss = card.englishGlosses.join(", ");
        const glossPart = gloss ? `(${gloss})` : "";
        const translation = card.sourceSentenceTranslation ? ` = ${card.sourceSentenceTranslation}` : "";
        return `${glossPart} ${card.sourceSentence} (${card.lemma})${translation}`;
      })
      .join("\n\n");

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
    const header = "Korean,English,POS,Level,Example Korean,Example English,Notes";
    const rows = cards.map((card) => {
      const escape = (s: string) => `"${s.replace(/"/g, '""')}"`;
      return [
        escape(card.lemma),
        escape(card.englishGlosses.join("; ")),
        escape(card.pos),
        escape(card.level || "unknown"),
        escape(card.sourceSentence),
        escape(card.sourceSentenceTranslation || ""),
        escape(card.reason),
      ].join(",");
    });
    downloadFile([header, ...rows].join("\n"), "vocab.csv", "text/csv");
  };

  const exportAnkiCSV = () => {
    const header = "Front,Back,Example,Level";
    const rows = cards.map((card) => {
      const escape = (s: string) => `"${s.replace(/"/g, '""')}"`;
      const front = escape(card.lemma);
      const gloss = card.englishGlosses.join("; ");
      const example = card.sourceSentenceTranslation
        ? `${card.sourceSentence}\n${card.sourceSentenceTranslation}`
        : card.sourceSentence;
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
        Copy all
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
