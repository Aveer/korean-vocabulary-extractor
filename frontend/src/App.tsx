import { useState, useEffect } from "react";
import {
  AppTheme,
  ExtractVocabRequest,
  ExtractVocabResponse,
  TargetLevel,
  VocabCard,
  DictionaryConfig,
  DictionaryProvider,
} from "./types";
import VocabCardComponent from "./components/VocabCard";
import ExportActions from "./components/ExportActions";
import DictionarySettings from "./components/DictionarySettings";
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

  // Theme state (persisted in localStorage)
  const [theme, setTheme] = useState<AppTheme>(
    (): AppTheme => (localStorage.getItem("theme") as AppTheme) || "light"
  );

  // Apply theme to document
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  // Dictionary config state
  const [dictConfig, setDictConfig] = useState<DictionaryConfig | null>(null);
  const [dictLoading, setDictLoading] = useState(true);

  // Fetch dictionary config on mount
  useEffect(() => {
    fetch("/api/dictionary-config")
      .then((res) => {
        if (!res.ok) throw new Error(`Config fetch failed: ${res.status}`);
        return res.json();
      })
      .then((data: DictionaryConfig) => setDictConfig(data))
      .catch(() => setDictConfig(null))
      .finally(() => setDictLoading(false));
  }, []);

  const handleSaveDictConfig = async (provider: DictionaryProvider, apiKey?: string) => {
    const response = await fetch("/api/dictionary-config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, api_key: apiKey }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Failed to save: ${response.status}`);
    }
    const updated: DictionaryConfig = await response.json();
    setDictConfig(updated);
  };

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

      <DictionarySettings
        config={dictConfig}
        loading={dictLoading}
        onSave={handleSaveDictConfig}
        theme={theme}
        onThemeChange={setTheme}
      />

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
