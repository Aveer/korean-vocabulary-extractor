import { useEffect, useRef, useState } from "react";
import { AppTheme, DictionaryConfig, DictionaryProvider } from "../types";

interface Props {
  config: DictionaryConfig | null;
  loading: boolean;
  onSave: (provider: DictionaryProvider, apiKey?: string) => void;
  theme: AppTheme;
  onThemeChange: (theme: AppTheme) => void;
}

export default function DictionarySettings({
  config,
  loading,
  onSave,
  theme,
  onThemeChange,
}: Props) {
  const [open, setOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<DictionaryProvider>(
    config?.provider || "bundled"
  );
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const providerTouchedRef = useRef(false);
  const apiKeyTouchedRef = useRef(false);

  useEffect(() => {
    if (saving || providerTouchedRef.current || apiKeyTouchedRef.current) {
      return;
    }

    const nextProvider = config?.provider || "bundled";
    setSelectedProvider((current) => (current === nextProvider ? current : nextProvider));
  }, [config?.provider, saving]);

  const hasChanges =
    (config && selectedProvider !== config.provider) ||
    (selectedProvider === "nikl" && apiKey !== "" && !config?.apiKeySet);

  const handleSave = async () => {
    setSaving(true);
    setStatus(null);
    try {
      await onSave(selectedProvider, selectedProvider === "nikl" ? apiKey || undefined : undefined);
      providerTouchedRef.current = false;
      apiKeyTouchedRef.current = false;
      setStatus({ type: "success", message: "Settings saved." });
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to save settings.",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleThemeToggle = () => {
    const next = theme === "light" ? "dark" : "light";
    onThemeChange(next);
  };

  return (
    <div className="settings-panel">
      <button
        className="settings-toggle"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        {open ? "▾" : "▸"} Settings
      </button>

      {open && (
        <div className="settings-body">
          <div className="settings-theme-row">
            <span className="settings-theme-label">Theme</span>
            <button className="theme-toggle-btn" onClick={handleThemeToggle}>
              {theme === "light" ? "☀️ Light" : "🌙 Dark"}
            </button>
          </div>

          <div className="provider-options">
            <label className={`provider-option ${selectedProvider === "bundled" ? "selected" : ""}`}>
              <input
                type="radio"
                name="provider"
                value="bundled"
                checked={selectedProvider === "bundled"}
                onChange={() => {
                  providerTouchedRef.current = true;
                  setSelectedProvider("bundled");
                  setStatus(null);
                }}
              />
              <span className="provider-label">
                Bundled (offline)
                {config?.bundledAvailable && (
                  <span className="provider-detail">
                    {config.bundledEntryCount.toLocaleString()} entries
                    {config.bundledSource && ` · ${config.bundledSource}`}
                  </span>
                )}
              </span>
            </label>

            <label className={`provider-option ${selectedProvider === "nikl" ? "selected" : ""}`}>
              <input
                type="radio"
                name="provider"
                value="nikl"
                checked={selectedProvider === "nikl"}
                onChange={() => {
                  providerTouchedRef.current = true;
                  setSelectedProvider("nikl");
                  setStatus(null);
                }}
              />
              <span className="provider-label">
                NIKL API
                {config?.apiKeySet && <span className="provider-detail">· Key configured</span>}
              </span>
            </label>
          </div>

          {selectedProvider === "nikl" && (
            <div className="api-key-section">
              <label htmlFor="apiKey">API Key</label>
              <div className="api-key-input-row">
                <div className="api-key-input-wrapper">
                  <input
                    id="apiKey"
                    type={showKey ? "text" : "password"}
                    placeholder="Paste your NIKL API key here"
                    value={apiKey}
                    onChange={(e) => {
                      apiKeyTouchedRef.current = true;
                      setApiKey(e.target.value);
                      setStatus(null);
                    }}
                  />
                  <button
                    type="button"
                    className="toggle-visibility"
                    onClick={() => setShowKey(!showKey)}
                    aria-label={showKey ? "Hide API key" : "Show API key"}
                  >
                    {showKey ? "🙈" : "👁"}
                  </button>
                </div>
              </div>
              <p className="api-key-instructions">
                Get a free API key at:{" "}
                <a href="https://www.korean.go.kr/portal/outer/main.do" target="_blank" rel="noopener noreferrer">
                  korean.go.kr
                </a>{" "}
                → Open API → Register → Copy your key here.
              </p>
            </div>
          )}

          <div className="settings-actions">
            <button
              className="save-btn"
              onClick={handleSave}
              disabled={!hasChanges || saving || loading}
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>

          {status && (
            <div className={`settings-status settings-status-${status.type}`}>
              {status.message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
