import { Upload, Database, CheckCircle2, ShieldAlert } from "lucide-react";

export function TopBar({ runManifest, sourceName, onOpenUpload }) {
  const scope = runManifest?.evaluation_scope || "synthetic_smoke";
  const datasetId = runManifest?.dataset_id || "unknown-dataset";
  const algorithm = runManifest?.algorithm || "unknown-algorithm";

  return (
    <header
      style={{
        height: "56px",
        background: "rgba(11, 16, 23, 0.8)",
        borderBottom: "1px solid var(--panel-border)",
        backdropFilter: "blur(12px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        position: "sticky",
        top: 0,
        zIndex: 40
      }}
    >
      {/* Left: Identification & Metadata */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-white)", letterSpacing: "0.05em" }}>
            SENTINEL PULSE
          </span>
          <span style={{ color: "var(--text-dim)", fontSize: "0.8rem" }}>/</span>
          <span className="mono-num" style={{ fontSize: "0.8rem", color: "var(--cyan-signal)" }}>
            {algorithm}
          </span>
        </div>

        {/* Mandatory Scope Badge */}
        <span className="scope-badge">
          <ShieldAlert size={11} />
          {scope}
        </span>

        {/* Dataset ID */}
        <div style={{ display: "flex", alignItems: "center", gap: "5px", color: "var(--text-muted)", fontSize: "0.75rem", fontFamily: "var(--font-mono)" }}>
          <Database size={13} style={{ color: "var(--text-dim)" }} />
          <span>{datasetId}</span>
        </div>

        {/* Provisional Metric Warning */}
        <span
          style={{
            fontSize: "0.68rem",
            color: "var(--text-dim)",
            fontFamily: "var(--font-mono)",
            background: "rgba(255,255,255,0.03)",
            padding: "2px 6px",
            borderRadius: "3px",
            border: "1px solid rgba(255,255,255,0.05)"
          }}
        >
          Metric: provisional_event_trigger_f1_v0 (not official)
        </span>
      </div>

      {/* Right: Data Source & Upload Button */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.76rem", color: "var(--text-muted)" }}>
          <CheckCircle2 size={13} style={{ color: "var(--cyan-signal)" }} />
          <span className="mono-num">{sourceName}</span>
        </div>

        <button
          className="btn-precision"
          onClick={onOpenUpload}
          style={{ padding: "6px 12px", fontSize: "0.78rem" }}
        >
          <Upload size={14} />
          <span>Load Run Artifacts</span>
        </button>
      </div>
    </header>
  );
}
