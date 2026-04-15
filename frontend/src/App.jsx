import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const ANALYSIS_STORAGE_KEY = "accessibility-rem-analysis";
const USAGE_STORAGE_KEY = "accessibility-rem-usage";
const DOC_RESULT_STORAGE_KEY = "accessibility-rem-doc-result";

function formatConfidence(value) {
  if (typeof value !== "number") return null;
  return `${Math.round(value * 100)}% confidence`;
}

function normalizeHeaders(tableData) {
  if (!tableData?.length) return { headers: [], rows: [] };
  const [rawHeaders, ...rows] = tableData;
  const seen = new Map();
  const headers = rawHeaders.map((header) => {
    const base = String(header || "Column").trim() || "Column";
    const next = (seen.get(base) || 0) + 1;
    seen.set(base, next);
    return next === 1 ? base : `${base}_${next}`;
  });
  return { headers, rows };
}

function App() {
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [usage, setUsage] = useState(null);
  const [docResult, setDocResult] = useState(null);
  const [isGoogleConnected, setIsGoogleConnected] = useState(false);
  const [isCheckingGoogleAuth, setIsCheckingGoogleAuth] = useState(true);
  const [error, setError] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isCreatingDoc, setIsCreatingDoc] = useState(false);

  const flaggedCount = useMemo(
    () => analysis?.items?.filter((item) => item.needs_review).length ?? 0,
    [analysis]
  );

  useEffect(() => {
    window.history.scrollRestoration = "manual";
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, []);

  useEffect(() => {
    try {
      const savedAnalysis = window.sessionStorage.getItem(ANALYSIS_STORAGE_KEY);
      const savedUsage = window.sessionStorage.getItem(USAGE_STORAGE_KEY);
      const savedDocResult = window.sessionStorage.getItem(DOC_RESULT_STORAGE_KEY);

      if (savedAnalysis) {
        setAnalysis(JSON.parse(savedAnalysis));
      }
      if (savedUsage) {
        setUsage(JSON.parse(savedUsage));
      }
      if (savedDocResult) {
        setDocResult(JSON.parse(savedDocResult));
      }
    } catch {
      window.sessionStorage.removeItem(ANALYSIS_STORAGE_KEY);
      window.sessionStorage.removeItem(USAGE_STORAGE_KEY);
      window.sessionStorage.removeItem(DOC_RESULT_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    if (analysis) {
      window.sessionStorage.setItem(ANALYSIS_STORAGE_KEY, JSON.stringify(analysis));
    } else {
      window.sessionStorage.removeItem(ANALYSIS_STORAGE_KEY);
    }
  }, [analysis]);

  useEffect(() => {
    if (usage) {
      window.sessionStorage.setItem(USAGE_STORAGE_KEY, JSON.stringify(usage));
    } else {
      window.sessionStorage.removeItem(USAGE_STORAGE_KEY);
    }
  }, [usage]);

  useEffect(() => {
    if (docResult) {
      window.sessionStorage.setItem(DOC_RESULT_STORAGE_KEY, JSON.stringify(docResult));
    } else {
      window.sessionStorage.removeItem(DOC_RESULT_STORAGE_KEY);
    }
  }, [docResult]);

  useEffect(() => {
    async function checkGoogleAuth() {
      try {
        const response = await fetch(`${API_BASE}/api/google-auth/status`, {
          credentials: "include"
        });
        const payload = await response.json();
        if (response.ok) {
          setIsGoogleConnected(Boolean(payload.connected));
        }
      } catch {
        setIsGoogleConnected(false);
      } finally {
        setIsCheckingGoogleAuth(false);
      }
    }

    const params = new URLSearchParams(window.location.search);
    const authState = params.get("google_auth");
    const authMessage = params.get("message");
    if (authState === "error" && authMessage) {
      setError(authMessage);
    }
    if (authState) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    checkGoogleAuth();
  }, []);

  function handleConnectGoogle() {
    window.location.href = `${API_BASE}/api/google-auth/start`;
  }

  async function handleAnalyze(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a PDF first.");
      return;
    }

    setIsAnalyzing(true);
    setError("");
    setDocResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        body: formData,
        credentials: "include"
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "PDF analysis failed.");
      }

      setAnalysis(payload.analysis);
      setUsage(payload.usage);
      setDocResult(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleCreateGoogleDoc() {
    if (!analysis) return;

    setIsCreatingDoc(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/create-google-doc`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ analysis })
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Google Doc creation failed.");
      }
      setDocResult(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsCreatingDoc(false);
    }
  }

  return (
    <div className="shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <header className="hero panel">
        <div>
          <p className="eyebrow">Accessibility Remediation</p>
          <h1 className="hero-title">PDF Remediation Hub</h1>
          <p className="lede">
            Upload a PDF, review figures and tables with page-level context,
            and then generate a pre-formatted Google Doc with accessible summaries and flags for complex content.
          </p>
        </div>
        <div className="hero-metrics">
          <div className="metric-card">
            <span className="metric-label">Items Found</span>
            <strong>{analysis?.items?.length ?? 0}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Flagged</span>
            <strong>{flaggedCount}</strong>
          </div>
        </div>
      </header>

      <main className="layout">
        <section className="panel upload-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">Step 1</p>
              <h2>Upload a PDF</h2>
            </div>
            <span className="status-chip">{file ? file.name : "No file selected"}</span>
          </div>

          <form onSubmit={handleAnalyze} className="upload-form">
            <label className="dropzone">
              <input
                type="file"
                accept="application/pdf"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
              <span className="dropzone-title">Choose remediation source</span>
              <span className="dropzone-copy">
                Browse through your files and select a PDF document to upload.
              </span>
            </label>

            <button className="primary-button" type="submit" disabled={!file || isAnalyzing}>
              {isAnalyzing ? "Analyzing..." : "Analyze PDF"}
            </button>
          </form>

          {usage ? (
            <div className="usage-strip">
              <span>Model: {usage.model}</span>
              <span>Input: {usage.input_tokens ?? "-"}</span>
              <span>Output: {usage.output_tokens ?? "-"}</span>
            </div>
          ) : null}

          {error ? <div className="error-banner">{error}</div> : null}
        </section>

        <aside className="panel action-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">Step 2</p>
              <h2>Create Google Doc</h2>
            </div>
          </div>

          <p className="panel-copy">
            Connect your Google account, then generate a remediation document with
            flags for complex items.
          </p>

          <div className="action-stack">
            <div className="action-row">
              <div className="google-status-row">
                <span className={`status-dot ${isGoogleConnected ? "" : "status-dot-pending"}`} aria-hidden="true" />
                <span className="google-status-copy">
                  {isCheckingGoogleAuth
                    ? "Checking Google connection..."
                    : isGoogleConnected
                      ? "Google account connected"
                      : "Google account not connected"}
                </span>
              </div>

              {!isGoogleConnected && !isCheckingGoogleAuth ? (
                <button
                  className="secondary-button action-button"
                  type="button"
                  onClick={handleConnectGoogle}
                >
                  Connect Google
                </button>
              ) : null}

              {isGoogleConnected && !isCreatingDoc && !docResult ? (
                <button
                  className="secondary-button action-button"
                  type="button"
                  disabled={!analysis}
                  onClick={handleCreateGoogleDoc}
                >
                  Create Google Doc
                </button>
              ) : null}
            </div>

            {isCreatingDoc ? (
              <div className="doc-result">
                <div className="doc-result-status">
                  <span className="status-dot status-dot-pending" aria-hidden="true" />
                  <span className="doc-result-label">Creating Google Doc...</span>
                </div>
              </div>
            ) : null}

            {docResult && !isCreatingDoc ? (
              <div className="doc-result">
                <div className="doc-result-status">
                  <span className="status-dot" aria-hidden="true" />
                  <span className="doc-result-label">Google Doc is ready</span>
                </div>
                <a
                  className="doc-link-button"
                  href={docResult.document_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open Google Doc
                </a>
              </div>
            ) : null}
          </div>
        </aside>
      </main>

      <section className="panel results-panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Analysis</p>
            <h2>{analysis ? analysis.title : "Results appear here after analysis"}</h2>
          </div>
        </div>

        {!analysis ? (
          <div className="empty-state">
            <p>No analysis loaded yet. Upload a PDF to inspect page locations, confidence, and extracted tables.</p>
          </div>
        ) : (
          <div className="items-grid">
            {analysis.items.map((item, index) => {
              const { headers, rows } = normalizeHeaders(item.table_data || []);
              return (
                <article
                  key={`${item.type}-${item.number ?? index}-${item.title}`}
                  className={`item-card ${item.needs_review ? "item-card-flagged" : ""}`}
                >
                  <div className="item-head">
                    <div>
                      <p className="item-kicker">
                        {item.type} {item.number ?? index + 1}
                      </p>
                      <h3>{item.title}</h3>
                    </div>
                    <div className="item-meta">
                      {item.page ? <span className="meta-pill">Page {item.page}</span> : null}
                      {item.needs_review ? <span className="meta-pill warning">Needs review</span> : null}
                    </div>
                  </div>

                  <p className="item-description">{item.description}</p>

                  <div className="item-foot">
                    {formatConfidence(item.confidence) ? (
                      <span className="meta-line">{formatConfidence(item.confidence)}</span>
                    ) : null}
                    {item.review_reason ? <span className="meta-line">{item.review_reason}</span> : null}
                  </div>

                  {headers.length ? (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            {headers.map((header) => (
                              <th key={header}>{header}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((row, rowIndex) => (
                            <tr key={rowIndex}>
                              {row.map((cell, cellIndex) => (
                                <td key={`${rowIndex}-${cellIndex}`}>{String(cell ?? "")}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        )}
      </section>

      <footer className="glass-footer" aria-label="Project attribution">
        <span className="glass-footer-mark">Prototype for Brown University DLD</span>
      </footer>
    </div>
  );
}

export default App;
