import { useState } from "react";
import { ExtractVocabRequest, ExtractVocabResponse, TargetLevel, VocabCard } from "./types";
import VocabCardComponent from "./components/VocabCard";
import ExportActions from "./components/ExportActions";
import "./App.css";

const TARGET_LEVELS: { value: TargetLevel; label: string }[] = [
  { value: "ANY", label: "Any TOPIK II level" },
  { value: "TOPIK_II_3", label: "TOPIK II Level 3" },
  { value: "TOPIK_II_4", label: "TOPIK II Level 4" },
  { value: "TOPIK_II_5", label: "TOPIK II Level 5" },
  { value: "TOPIK_II_6", label: "TOPIK II Level 6" },
];

export default function App() {
  const [text, setText] = useState("");
  const [targetLevel, setTargetLevel] = useState<TargetLevel>("ANY");
  const [wordCount, setWordCount] = useState(20);
  const [cards, setCards] = useState<VocabCard[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExtract = async () => {
    if (!text.trim()) {
      setError("Please paste Korean text first.");
      return;
    }

    setLoading(true);
    setError(null);
    setCards(null);

    const request: ExtractVocabRequest = {
      text: text.trim(),
      targetLevel,
      wordCount,
      includeSentenceTranslation: true,
    };

    try {
      const response = await fetch("/api/extract-vocab", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Server error: ${response.status}`);
      }

      const data: ExtractVocabResponse = await response.json();
      setCards(data.cards);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not extract vocabulary from this passage.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Korean Vocab Extractor</h1>
        <p className="subtitle">Paste Korean text and extract study-ready vocabulary.</p>
      </header>

      <div className="input-section">
        <div className="controls">
          <div className="control-group">
            <label htmlFor="wordCount">Number of words</label>
            <input
              id="wordCount"
              type="number"
              min={1}
              max={100}
              value={wordCount}
              onChange={(e) => setWordCount(Math.max(1, Math.min(100, Number(e.target.value) || 20)))}
            />
          </div>

          <div className="control-group">
            <label htmlFor="targetLevel">Target level</label>
            <select id="targetLevel" value={targetLevel} onChange={(e) => setTargetLevel(e.target.value as TargetLevel)}>
              {TARGET_LEVELS.map((level) => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <textarea
          className="text-input"
          placeholder="Paste a chapter or passage of Korean text here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
        />

        <button className="extract-btn" onClick={handleExtract} disabled={loading}>
          {loading ? "Extracting vocabulary..." : "Extract vocabulary"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {cards && cards.length > 0 && (
        <section className="results">
          <div className="results-header">
            <h2>Results ({cards.length} words)</h2>
            <ExportActions cards={cards} />
          </div>
          <div className="cards">
            {cards.map((card, index) => (
              <VocabCardComponent key={`${card.lemma}-${index}`} card={card} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
