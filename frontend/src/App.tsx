import { useState, useEffect } from "react";
import {
  AppTheme,
  DueReviewCard,
  ExtractVocabRequest,
  ExtractVocabResponse,
  ReviewRating,
  SavedStudyCard,
  StudyStats,
  TargetLevel,
  VocabCard,
  DictionaryConfig,
  DictionaryProvider,
} from "./types";
import VocabCardComponent from "./components/VocabCard";
import ExportActions from "./components/ExportActions";
import DictionarySettings from "./components/DictionarySettings";
import ReadingHighlights from "./components/ReadingHighlights";
import "./App.css";

const TARGET_LEVELS: { value: TargetLevel; label: string }[] = [
  { value: "ANY", label: "Any TOPIK II level" },
  { value: "TOPIK_II_3", label: "TOPIK II Level 3" },
  { value: "TOPIK_II_4", label: "TOPIK II Level 4" },
  { value: "TOPIK_II_5", label: "TOPIK II Level 5" },
  { value: "TOPIK_II_6", label: "TOPIK II Level 6" },
];

type AppTab = "extract" | "deck" | "review" | "progress";

const TABS: { value: AppTab; label: string }[] = [
  { value: "extract", label: "Extract" },
  { value: "deck", label: "Deck" },
  { value: "review", label: "Review" },
  { value: "progress", label: "Progress" },
];

const getLevelProgress = (xp: number, level: number) => {
  // Backend level formula: level = 1 + int(sqrt(xp // 25)).
  const currentLevelStart = Math.max(0, Math.pow(Math.max(0, level - 1), 2) * 25);
  const nextLevelAt = Math.max(currentLevelStart + 25, Math.pow(level, 2) * 25);
  const earnedThisLevel = Math.max(0, xp - currentLevelStart);
  const neededThisLevel = Math.max(1, nextLevelAt - currentLevelStart);

  return {
    currentLevelStart,
    nextLevelAt,
    percent: Math.min(100, Math.round((earnedThisLevel / neededThisLevel) * 100)),
  };
};

const REVIEW_LABELS: Record<ReviewRating, string> = {
  again: "Again / Forgot",
  hard: "Hard / Almost",
  good: "Good / Got it",
  easy: "Easy / Instant",
};

export default function App() {
  const [text, setText] = useState("");
  const [targetLevel, setTargetLevel] = useState<TargetLevel>("ANY");
  const [wordCount, setWordCount] = useState(20);
  const [cards, setCards] = useState<VocabCard[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<AppTab>("extract");
  const [stats, setStats] = useState<StudyStats | null>(null);
  const [studyError, setStudyError] = useState<string | null>(null);
  const [deckCards, setDeckCards] = useState<SavedStudyCard[]>([]);
  const [deckLoading, setDeckLoading] = useState(false);
  const [dueCards, setDueCards] = useState<DueReviewCard[]>([]);
  const [dueCount, setDueCount] = useState(0);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [completedReviews, setCompletedReviews] = useState(0);
  const [lastXpGained, setLastXpGained] = useState<number | null>(null);
  const [excludeKnown, setExcludeKnown] = useState(true);
  const [excludeIgnored, setExcludeIgnored] = useState(true);

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

  const refreshStats = async () => {
    try {
      const response = await fetch("/api/study/stats");
      if (!response.ok) throw new Error(`Stats unavailable: ${response.status}`);
      const data: StudyStats = await response.json();
      setStats(data);
    } catch {
      setStats(null);
    }
  };

  const refreshDeck = async () => {
    setDeckLoading(true);
    try {
      const response = await fetch("/api/study/cards");
      if (!response.ok) throw new Error(`Deck unavailable: ${response.status}`);
      const data = await response.json();
      setDeckCards(data.cards || []);
    } catch (err) {
      setStudyError(err instanceof Error ? err.message : "Could not load deck.");
    } finally {
      setDeckLoading(false);
    }
  };

  const refreshDue = async () => {
    setReviewLoading(true);
    try {
      const response = await fetch("/api/study/reviews/due?limit=20");
      if (!response.ok) throw new Error(`Reviews unavailable: ${response.status}`);
      const data = await response.json();
      setDueCards(data.cards || []);
      setDueCount(data.dueCount || 0);
      setRevealed(false);
      return data;
    } catch (err) {
      setStudyError(err instanceof Error ? err.message : "Could not load reviews.");
      return null;
    } finally {
      setReviewLoading(false);
    }
  };

  useEffect(() => {
    refreshStats();
    refreshDeck();
    refreshDue();
  }, []);

  useEffect(() => {
    if (activeTab === "deck") refreshDeck();
    if (activeTab === "review") refreshDue();
  }, [activeTab]);

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
      excludeKnown,
      excludeIgnored,
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

  const saveCard = async (card: VocabCard): Promise<SavedStudyCard> => {
    const response = await fetch("/api/study/cards", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(card),
    });
    if (!response.ok) throw new Error(`Could not save ${card.lemma}: ${response.status}`);
    return response.json();
  };

  const handleSaveCard = async (card: VocabCard) => {
    setStudyError(null);
    try {
      const saved = await saveCard(card);
      setCards((current) =>
        current?.map((item) =>
          item.lemma === card.lemma ? { ...item, studyStatus: "new", savedCardId: saved.id } : item
        ) || null
      );
      await Promise.all([refreshStats(), refreshDeck(), refreshDue()]);
    } catch (err) {
      setStudyError(err instanceof Error ? err.message : "Could not save card.");
    }
  };

  const getSaveableCards = (sourceCards = cards || []) =>
    sourceCards.filter((card) => card.savedCardId == null && card.studyStatus !== "known" && card.studyStatus !== "ignored");

  const handleSaveAll = async (options: { refreshAfter?: boolean } = {}) => {
    if (!cards?.length) return [];
    setStudyError(null);
    try {
      const unsaved = getSaveableCards(cards);
      const saved = await Promise.all(unsaved.map(saveCard));
      const savedByLemma = new Map(saved.map((card) => [card.lemma, card]));
      setCards((current) =>
        current?.map((card) => {
          const savedCard = savedByLemma.get(card.lemma);
          return savedCard ? { ...card, studyStatus: "new", savedCardId: savedCard.id } : card;
        }) || null
      );
      if (options.refreshAfter !== false) {
        await Promise.all([refreshStats(), refreshDeck(), refreshDue()]);
      }
      return saved;
    } catch (err) {
      setStudyError(err instanceof Error ? err.message : "Could not save all cards.");
      return [];
    }
  };

  const handleSaveAllAndReview = async () => {
    if (!cards?.length) return;
    await handleSaveAll({ refreshAfter: false });
    await Promise.all([refreshStats(), refreshDeck(), refreshDue()]);
    setActiveTab("review");
  };

  const setLemmaStatus = async (lemma: string, status: "new" | "known" | "ignored") => {
    setStudyError(null);
    try {
      const response = await fetch(`/api/study/lemmas/${encodeURIComponent(lemma)}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) throw new Error(`Could not mark ${lemma}: ${response.status}`);
      setCards((current) => current?.map((card) => (card.lemma === lemma ? { ...card, studyStatus: status } : card)) || null);
      await Promise.all([refreshStats(), refreshDeck(), refreshDue()]);
    } catch (err) {
      setStudyError(err instanceof Error ? err.message : "Could not update lemma.");
    }
  };

  const removeSavedCard = async (id: string | number) => {
    setStudyError(null);
    try {
      const response = await fetch(`/api/study/cards/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error(`Could not remove card: ${response.status}`);
      setDeckCards((current) => current.filter((card) => card.id !== id));
      setCards((current) => current?.map((card) => (card.savedCardId === id ? { ...card, savedCardId: null } : card)) || null);
      await Promise.all([refreshStats(), refreshDue()]);
    } catch (err) {
      setStudyError(err instanceof Error ? err.message : "Could not remove card.");
    }
  };

  const submitReview = async (cardId: string | number, rating: ReviewRating) => {
    setStudyError(null);
    try {
      const response = await fetch(`/api/study/reviews/${cardId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating }),
      });
      if (!response.ok) throw new Error(`Review failed: ${response.status}`);
      const result = await response.json().catch(() => null);
      setLastXpGained(typeof result?.xpGained === "number" ? result.xpGained : null);
      setCompletedReviews((current) => current + 1);
      setRevealed(false);
      await Promise.all([refreshStats(), refreshDeck(), refreshDue()]);
    } catch (err) {
      setStudyError(err instanceof Error ? err.message : "Could not submit review.");
    }
  };

  const renderExtractActions = (card: VocabCard) => (
    <>
      <button className="chip-btn primary" onClick={() => handleSaveCard(card)} disabled={card.savedCardId != null || card.studyStatus === "known" || card.studyStatus === "ignored"}>
        {card.savedCardId != null ? "Saved" : "Save"}
      </button>
      <button className="chip-btn" onClick={() => setLemmaStatus(card.lemma, "known")}>Known</button>
      <button className="chip-btn ghost" onClick={() => setLemmaStatus(card.lemma, "ignored")}>Ignore</button>
    </>
  );

  const currentReview = dueCards[0];
  const saveableCount = getSaveableCards().length;
  const hasReviewableExtractedCards = Boolean(cards?.some((card) => card.savedCardId != null));
  const levelProgress = stats ? getLevelProgress(stats.xp, stats.level) : { currentLevelStart: 0, nextLevelAt: 25, percent: 0 };

  return (
    <div className="app">
      <header className="header">
        <h1>Korean Vocab Extractor</h1>
        <p className="subtitle">Turn any Korean passage into a mini study quest.</p>
        {stats && (
          <div className="stats-strip" aria-label="Study stats">
            <span>🔥 {stats.currentStreakDays} day streak</span>
            <span>✨ {stats.xp} XP</span>
            <span>🃏 {stats.totalCards} saved</span>
            <span>⏰ {stats.dueCount} due</span>
          </div>
        )}
      </header>

      <nav className="app-tabs" aria-label="App sections">
        {TABS.map((tab) => (
          <button key={tab.value} className={activeTab === tab.value ? "active" : ""} onClick={() => setActiveTab(tab.value)}>
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === "extract" && <>
      <div className="input-section panel-card">
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

          <label className="toggle-pill">
            <input type="checkbox" checked={excludeKnown} onChange={(e) => setExcludeKnown(e.target.checked)} />
            Skip known
          </label>

          <label className="toggle-pill">
            <input type="checkbox" checked={excludeIgnored} onChange={(e) => setExcludeIgnored(e.target.checked)} />
            Skip ignored
          </label>
        </div>

        <label className="passage-label" htmlFor="korean-passage">Korean passage</label>
        <textarea
          id="korean-passage"
          className="text-input"
          placeholder="Paste a chapter or passage of Korean text here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
        />

        <button className="extract-btn" onClick={handleExtract} disabled={loading}>
          {loading ? "Scouting quest words..." : "Start extraction quest"}
        </button>
      </div>

      <DictionarySettings
        config={dictConfig}
        loading={dictLoading}
        onSave={handleSaveDictConfig}
        theme={theme}
        onThemeChange={setTheme}
      />
      </>}

      {error && <div className="error">{error}</div>}
      {studyError && <div className="error">{studyError}</div>}

      {activeTab === "extract" && cards && cards.length === 0 && !loading && (
        <section className="empty-results" aria-live="polite">
          <div className="empty-results-mark" aria-hidden="true">
            빈
          </div>
          <div className="empty-results-copy">
            <h2>No vocabulary cards found</h2>
            <p>
              Try pasting a little more clear Korean text, or switch to a different TOPIK level to widen the match.
            </p>
          </div>
        </section>
      )}

      {activeTab === "extract" && cards && cards.length > 0 && (
        <section className="results">
          <div className="results-header">
            <div>
              <div className="section-kicker">Loot found</div>
              <h2>Quest cards ({cards.length})</h2>
            </div>
            <div className="results-actions">
              <button className="export-btn primary" onClick={handleSaveAllAndReview} disabled={saveableCount === 0 && !hasReviewableExtractedCards}>
                {saveableCount > 0 ? "Save all & review" : "Review saved cards"}
              </button>
              <button className="export-btn" onClick={() => handleSaveAll()} disabled={saveableCount === 0}>
                {saveableCount > 0 ? "Save all to deck" : "All saveable cards saved"}
              </button>
              <ExportActions cards={cards} />
            </div>
          </div>
          <ReadingHighlights text={text} cards={cards} />
          <div className="cards">
            {cards.map((card, index) => (
              <VocabCardComponent key={`${card.lemma}-${index}`} card={card} actions={renderExtractActions(card)} />
            ))}
          </div>
        </section>
      )}

      {activeTab === "deck" && (
        <section className="panel-card deck-view">
          <div className="results-header">
            <div>
              <div className="section-kicker">Your armory</div>
              <h2>Saved deck</h2>
            </div>
            <button className="export-btn primary" onClick={() => setActiveTab("review")}>Review due ({stats?.dueCount ?? dueCount})</button>
          </div>
          {deckLoading && <p className="muted">Loading saved cards...</p>}
          {!deckLoading && deckCards.length === 0 && <div className="empty-state">No cards saved yet. Extract a passage and bank your first quest words.</div>}
          <div className="cards">
            {deckCards.map((card) => (
              <VocabCardComponent key={card.id} card={card} actions={<button className="chip-btn ghost" onClick={() => removeSavedCard(card.id)}>Remove</button>} />
            ))}
          </div>
        </section>
      )}

      {activeTab === "review" && (
        <section className="panel-card review-view">
          <div className="section-kicker">Due queue</div>
          <h2>Review battle</h2>
          {reviewLoading && <p className="muted">Summoning due cards...</p>}
          {!reviewLoading && !currentReview && (
            <div className="completion-card">
              <h3>Quest complete</h3>
              <p>{completedReviews > 0 ? `Nice run — ${completedReviews} reviews cleared this session. Your XP is warming up.` : "No due cards right now. Save more words or come back later."}</p>
              {lastXpGained !== null && <p className="xp-feedback">+{lastXpGained} XP from your last review</p>}
              <button className="export-btn primary" onClick={() => setActiveTab("extract")}>Find new words</button>
            </div>
          )}
          {currentReview && (
            <div className="review-card">
              <div className="review-count">{dueCount} due · {completedReviews} cleared this session</div>
              <div className="card-meta-inline review-meta">
                <span className="badge badge-pos">{currentReview.pos}</span>
                {currentReview.level && currentReview.level !== "unknown" && <span className="badge badge-level">{currentReview.level}</span>}
              </div>
              <div className="review-prompt">{currentReview.lemma}</div>
              <div className="review-context">{currentReview.sourceFragment}</div>
              {lastXpGained !== null && <div className="xp-feedback" aria-live="polite">+{lastXpGained} XP gained on the last card</div>}
              {!revealed ? (
                <button className="extract-btn" onClick={() => setRevealed(true)}>Reveal answer</button>
              ) : (
                <>
                  <div className="answer-panel">
                    <strong>{currentReview.englishGlosses.join("; ") || "No gloss available"}</strong>
                    {currentReview.sourceFragmentTranslation && <p>{currentReview.sourceFragmentTranslation}</p>}
                  </div>
                  <div className="rating-grid">
                    {(["again", "hard", "good", "easy"] as ReviewRating[]).map((rating) => (
                      <button key={rating} className={`rating-btn ${rating}`} onClick={() => submitReview(currentReview.id, rating)}>{REVIEW_LABELS[rating]}</button>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      )}

      {activeTab === "progress" && (
        <section className="panel-card progress-view">
          <div className="section-kicker">Guild ledger</div>
          <h2>Level {stats?.level ?? 1} language hunter</h2>
          <div className="level-bar" aria-label={`Level progress: ${levelProgress.percent}%`}><span style={{ width: `${levelProgress.percent}%` }} /></div>
          <p className="level-copy">{stats?.xp ?? 0} XP · next level around {levelProgress.nextLevelAt} XP</p>
          <div className="progress-grid">
            <div><strong>{stats?.todayReviews ?? 0}</strong><span>reviews today</span></div>
            <div><strong>{stats?.knownLemmas ?? 0}</strong><span>known lemmas</span></div>
            <div><strong>{stats?.ignoredLemmas ?? 0}</strong><span>ignored</span></div>
            <div><strong>{stats?.totalCards ?? 0}</strong><span>deck cards</span></div>
          </div>
          <div className="quest-list">
            <h3>Daily quests</h3>
            <p className={(stats?.todayReviews ?? 0) > 0 ? "done" : ""}>Review at least one due card</p>
            <p className={(stats?.totalCards ?? 0) >= 10 ? "done" : ""}>Build a 10-card deck</p>
            <p className={(stats?.currentStreakDays ?? 0) > 0 ? "done" : ""}>Keep your streak alive</p>
          </div>
        </section>
      )}
    </div>
  );
}
