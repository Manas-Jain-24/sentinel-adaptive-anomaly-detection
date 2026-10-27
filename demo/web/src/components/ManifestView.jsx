import { useState } from "react";
import { Check, Copy, ShieldCheck, ShieldAlert, Cpu, Terminal, FileText, Lock, RefreshCw } from "lucide-react";
import { sha256Browser } from "../lib/hashing";

export function ManifestView({ runManifest, predictions = [] }) {
  const [copiedKey, setCopiedKey] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null); // true, false, null

  const handleCopy = (key, text) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleVerifyPredictions = async () => {
    if (!runManifest?.predictions_sha256 || predictions.length === 0) return;
    setVerifying(true);
    setVerificationResult(null);

    try {
      // Re-serialize predictions to JSONL format exactly as created
      const lines = predictions.map(p => {
        const raw = {
          series_id: p.series_id,
          timestamp: p.timestamp,
          value: p.value,
          score: p.score,
          threshold: p.threshold,
          label: p.label,
          ready: p.ready,
          evidence: p.evidence,
          schema_version: p.schema_version,
          elapsed_ns: p.elapsed_ns
        };
        return JSON.stringify(raw);
      });
      const content = lines.join("\n") + "\n";
      const computedHash = await sha256Browser(content);

      setTimeout(() => {
        setVerifying(false);
        // Compare with manifest
        const matches = computedHash.toLowerCase() === runManifest.predictions_sha256.toLowerCase();
        setVerificationResult(matches);
      }, 600);
    } catch (e) {
      console.error("Verification failed:", e);
      setVerifying(false);
      setVerificationResult(false);
    }
  };

  if (!runManifest) {
    return (
      <div className="glass-panel" style={{ padding: "40px", textAlign: "center" }}>
        <p style={{ color: "var(--text-muted)" }}>No run manifest loaded.</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Integrity Card */}
      <div className="glass-panel" style={{ padding: "24px 28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
          <div>
            <span style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-white)" }}>
              CRYPTOGRAPHIC RUN MANIFEST & INTEGRITY
            </span>
            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "3px" }}>
              Verifies zero data tampering and enforces immutable provenance for Challenge 2 submission.
            </p>
          </div>

          <button
            className={`btn-precision ${verificationResult === true ? "btn-primary" : verificationResult === false ? "btn-danger" : ""}`}
            onClick={handleVerifyPredictions}
            disabled={verifying}
            style={{ padding: "8px 16px" }}
          >
            <Lock size={15} />
            <span>{verifying ? "Computing Hash..." : verificationResult === true ? "SHA-256 MATCHED" : verificationResult === false ? "HASH MISMATCH" : "Verify SHA-256"}</span>
          </button>
        </div>

        {/* SHA-256 Chips */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          {/* Input Hash */}
          <div style={{ padding: "14px 18px", background: "rgba(5,7,10,0.6)", borderRadius: "var(--radius-sm)", border: "1px solid var(--panel-border)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>INPUT CSV SHA-256</span>
              <button
                className="btn-precision"
                onClick={() => handleCopy("input", runManifest.input_sha256)}
                style={{ padding: "2px 8px", fontSize: "0.68rem" }}
              >
                {copiedKey === "input" ? <Check size={12} style={{ color: "var(--cyan-signal)" }} /> : <Copy size={12} />}
                <span>{copiedKey === "input" ? "COPIED" : "COPY"}</span>
              </button>
            </div>
            <div className="mono-num" style={{ fontSize: "0.8rem", color: "var(--cyan-signal)", wordBreak: "break-all", marginTop: "8px" }}>
              {runManifest.input_sha256 || "N/A"}
            </div>
          </div>

          {/* Predictions Hash */}
          <div style={{ padding: "14px 18px", background: "rgba(5,7,10,0.6)", borderRadius: "var(--radius-sm)", border: "1px solid var(--panel-border)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>PREDICTIONS JSONL SHA-256</span>
                {verificationResult === true && <ShieldCheck size={14} style={{ color: "var(--cyan-signal)" }} />}
                {verificationResult === false && <ShieldAlert size={14} style={{ color: "var(--red-anomaly)" }} />}
              </div>
              <button
                className="btn-precision"
                onClick={() => handleCopy("pred", runManifest.predictions_sha256)}
                style={{ padding: "2px 8px", fontSize: "0.68rem" }}
              >
                {copiedKey === "pred" ? <Check size={12} style={{ color: "var(--cyan-signal)" }} /> : <Copy size={12} />}
                <span>{copiedKey === "pred" ? "COPIED" : "COPY"}</span>
              </button>
            </div>
            <div className="mono-num" style={{ fontSize: "0.8rem", color: "var(--amber-threshold)", wordBreak: "break-all", marginTop: "8px" }}>
              {runManifest.predictions_sha256 || "N/A"}
            </div>
          </div>
        </div>
      </div>

      {/* Manifest Key-Value Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Environment & Hardware */}
        <div className="glass-panel" style={{ padding: "20px 24px" }}>
          <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-white)", letterSpacing: "0.04em", marginBottom: "14px" }}>
            RUNTIME & HARDWARE SPECS
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "0.78rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "6px" }}>
              <span style={{ color: "var(--text-dim)" }}>Python Version:</span>
              <span className="mono-num" style={{ color: "var(--text-white)" }}>{runManifest.python}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "6px" }}>
              <span style={{ color: "var(--text-dim)" }}>Platform Architecture:</span>
              <span className="mono-num" style={{ color: "var(--text-white)" }}>{runManifest.platform}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "6px" }}>
              <span style={{ color: "var(--text-dim)" }}>Detector Total Runtime:</span>
              <span className="mono-num" style={{ color: "var(--cyan-signal)" }}>{(runManifest.detector_total_ns / 1000).toFixed(1)} µs</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "6px" }}>
              <span style={{ color: "var(--text-dim)" }}>Official Submission Ready:</span>
              <span className="mono-num" style={{ color: runManifest.official_submission_ready ? "var(--cyan-signal)" : "var(--amber-threshold)" }}>
                {runManifest.official_submission_ready ? "TRUE" : "FALSE (SYNTHETIC DEV)"}
              </span>
            </div>
          </div>
        </div>

        {/* Resolved Config */}
        <div className="glass-panel" style={{ padding: "20px 24px" }}>
          <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-white)", letterSpacing: "0.04em", marginBottom: "14px" }}>
            RESOLVED ALGORITHM CONFIG
          </div>
          <pre
            style={{
              padding: "12px",
              background: "rgba(5,7,10,0.7)",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--panel-border)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.78rem",
              color: "var(--text-white)",
              overflowX: "auto"
            }}
          >
            {JSON.stringify(runManifest.config, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

export function FigureShelf({ figures = [], onDownload }) {
  if (figures.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: "48px 24px", textAlign: "center" }}>
        <p style={{ color: "var(--text-white)", fontSize: "1.05rem", fontWeight: 600 }}>
          Figure Shelf is Empty
        </p>
        <p style={{ color: "var(--text-muted)", fontSize: "0.82rem", marginTop: "6px" }}>
          Use the "Capture for Slides" button on the Stream Viewer or Leaderboard charts to generate high-resolution, provenance-stamped 2x PNG figures for your 10-slide competition deck.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: "24px 28px" }}>
      <div style={{ marginBottom: "20px" }}>
        <span style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-white)" }}>
          FIGURE SHELF (10-SLIDE DECK EXPORTS)
        </span>
        <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "4px" }}>
          Each exported figure is rendered at 2x resolution and stamped with Run ID, Commit SHA, and Scope badge for traceability.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "20px" }}>
        {figures.map((fig, idx) => (
          <div
            key={idx}
            style={{
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--panel-border)",
              overflow: "hidden",
              background: "rgba(5,7,10,0.8)"
            }}
          >
            <img src={fig.url} alt={fig.filename} style={{ width: "100%", height: "160px", objectFit: "cover", display: "block" }} />
            <div style={{ padding: "12px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div className="mono-num" style={{ fontSize: "0.78rem", color: "var(--text-white)", fontWeight: 600 }}>
                  {fig.filename}
                </div>
                <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", marginTop: "2px" }}>
                  {fig.timestamp}
                </div>
              </div>
              <a href={fig.url} download={fig.filename} className="btn-precision" style={{ padding: "4px 10px", fontSize: "0.72rem" }}>
                Download
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function UploadModal({ isOpen, onClose, onUpload }) {
  const [dragActive, setDragActive] = useState(false);

  if (!isOpen) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(Array.from(e.dataTransfer.files));
      onClose();
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(Array.from(e.target.files));
      onClose();
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 999,
        background: "rgba(5,7,10,0.85)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: "520px",
          padding: "32px",
          background: "#080c12"
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-white)", marginBottom: "8px" }}>
          Load Custom Run Artifacts
        </h3>
        <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "20px", lineHeight: 1.5 }}>
          Drop <code>predictions.jsonl</code>, <code>run.json</code>, <code>windows.json</code>, <code>evaluation.json</code>, or <code>results.jsonl/csv</code>. The browser parses all contracts client-side without any backend.
        </p>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${dragActive ? "var(--cyan-signal)" : "rgba(255,255,255,0.15)"}`,
            borderRadius: "var(--radius-md)",
            padding: "40px 20px",
            textAlign: "center",
            background: dragActive ? "rgba(61,242,224,0.05)" : "transparent",
            cursor: "pointer",
            transition: "all var(--transition-fast)"
          }}
          onClick={() => document.getElementById("file-upload-input").click()}
        >
          <p style={{ color: "var(--cyan-signal)", fontWeight: 600, fontSize: "0.95rem" }}>
            Click to Browse or Drag & Drop Files Here
          </p>
          <p style={{ color: "var(--text-dim)", fontSize: "0.75rem", marginTop: "6px" }}>
            Supports JSONL, JSON, CSV files
          </p>
          <input
            id="file-upload-input"
            type="file"
            multiple
            style={{ display: "none" }}
            onChange={handleChange}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "24px" }}>
          <button className="btn-precision" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export function HelpModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 999,
        background: "rgba(5,7,10,0.85)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: "480px",
          padding: "28px",
          background: "#080c12"
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-white)", marginBottom: "16px" }}>
          Keyboard Shortcuts (Precision Terminal)
        </h3>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "0.82rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "6px" }}>
            <span style={{ color: "var(--text-muted)" }}>Play / Pause Replay:</span>
            <kbd style={{ background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "3px", fontFamily: "var(--font-mono)" }}>Space</kbd>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "6px" }}>
            <span style={{ color: "var(--text-muted)" }}>Step Forward / Backward:</span>
            <kbd style={{ background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "3px", fontFamily: "var(--font-mono)" }}>? / ?</kbd>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "6px" }}>
            <span style={{ color: "var(--text-muted)" }}>Jump to Next Anomaly:</span>
            <kbd style={{ background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "3px", fontFamily: "var(--font-mono)" }}>]</kbd>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "6px" }}>
            <span style={{ color: "var(--text-muted)" }}>Jump to Previous Anomaly:</span>
            <kbd style={{ background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "3px", fontFamily: "var(--font-mono)" }}>[</kbd>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "6px" }}>
            <span style={{ color: "var(--text-muted)" }}>Open Evidence Inspector:</span>
            <kbd style={{ background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "3px", fontFamily: "var(--font-mono)" }}>E</kbd>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "6px" }}>
            <span style={{ color: "var(--text-muted)" }}>Zoom / Pan Chart:</span>
            <span className="mono-num" style={{ color: "var(--cyan-signal)" }}>Mouse Wheel / Drag</span>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "24px" }}>
          <button className="btn-precision" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}