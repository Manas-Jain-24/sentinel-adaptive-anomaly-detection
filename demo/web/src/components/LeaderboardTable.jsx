import { useState } from "react";
import { Crown, ArrowUpDown, ExternalLink } from "lucide-react";

export function LeaderboardTable({ results = [], onSelectRun }) {
  const [sortField, setSortField] = useState("event_f1");
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (field) => {
    if (sortField === field) setSortAsc(!sortAsc);
    else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sorted = [...results].sort((a, b) => {
    const vA = a[sortField] ?? -Infinity;
    const vB = b[sortField] ?? -Infinity;
    if (vA < vB) return sortAsc ? -1 : 1;
    if (vA > vB) return sortAsc ? 1 : -1;
    return 0;
  });

  return (
    <div className="glass-panel" style={{ padding: "20px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-white)", letterSpacing: "0.04em" }}>
            EVALUATION LEADERBOARD & MODEL BENCHMARK
          </span>
          <p style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "2px" }}>
            Sorted by event F1; measures causal accuracy vs. delay vs. throughput trade-offs.
          </p>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--panel-border)", color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "0.72rem" }}>
              <th style={{ padding: "10px 12px" }}>MODEL</th>
              <th style={{ padding: "10px 12px", cursor: "pointer" }} onClick={() => handleSort("event_f1")}>
                EVENT F1 <ArrowUpDown size={11} style={{ display: "inline" }} />
              </th>
              <th style={{ padding: "10px 12px", cursor: "pointer" }} onClick={() => handleSort("precision")}>
                PRECISION <ArrowUpDown size={11} style={{ display: "inline" }} />
              </th>
              <th style={{ padding: "10px 12px", cursor: "pointer" }} onClick={() => handleSort("recall")}>
                RECALL <ArrowUpDown size={11} style={{ display: "inline" }} />
              </th>
              <th style={{ padding: "10px 12px", cursor: "pointer" }} onClick={() => handleSort("mean_delay_sec")}>
                MEAN DELAY <ArrowUpDown size={11} style={{ display: "inline" }} />
              </th>
              <th style={{ padding: "10px 12px", cursor: "pointer" }} onClick={() => handleSort("latency_us")}>
                LATENCY (µS) <ArrowUpDown size={11} style={{ display: "inline" }} />
              </th>
              <th style={{ padding: "10px 12px" }}>THROUGHPUT</th>
              <th style={{ padding: "10px 12px" }}>COMMIT</th>
              <th style={{ padding: "10px 12px" }}>STATUS</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((m, idx) => {
              const isWinner = m.is_winner || idx === 0;
              return (
                <tr
                  key={m.model_id || idx}
                  onClick={() => onSelectRun && onSelectRun(m)}
                  style={{
                    borderBottom: "1px solid rgba(255,255,255,0.04)",
                    cursor: "pointer",
                    background: isWinner ? "rgba(61, 242, 224, 0.04)" : "transparent",
                    transition: "background var(--transition-fast)"
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.04)"}
                  onMouseLeave={(e) => e.currentTarget.style.background = isWinner ? "rgba(61, 242, 224, 0.04)" : "transparent"}
                >
                  <td style={{ padding: "12px", fontWeight: 600, color: isWinner ? "var(--cyan-signal)" : "var(--text-white)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      {isWinner && <Crown size={14} style={{ color: "var(--amber-threshold)" }} />}
                      <span>{m.model_name || m.model_id}</span>
                    </div>
                  </td>
                  <td className="mono-num" style={{ padding: "12px", fontWeight: 700, color: isWinner ? "var(--cyan-signal)" : "var(--text-white)" }}>
                    {typeof m.event_f1 === "number" ? m.event_f1.toFixed(3) : "N/A"}
                  </td>
                  <td className="mono-num" style={{ padding: "12px", color: "var(--text-muted)" }}>
                    {typeof m.precision === "number" ? m.precision.toFixed(3) : "N/A"}
                  </td>
                  <td className="mono-num" style={{ padding: "12px", color: "var(--text-muted)" }}>
                    {typeof m.recall === "number" ? m.recall.toFixed(3) : "N/A"}
                  </td>
                  <td className="mono-num" style={{ padding: "12px", color: "var(--text-muted)" }}>
                    {typeof m.mean_delay_sec === "number" ? `${m.mean_delay_sec.toFixed(1)}s` : "N/A"}
                  </td>
                  <td className="mono-num" style={{ padding: "12px", color: "var(--text-muted)" }}>
                    {typeof m.latency_us === "number" ? `${m.latency_us.toFixed(1)} µs` : "N/A"}
                  </td>
                  <td className="mono-num" style={{ padding: "12px", color: "var(--text-muted)" }}>
                    {m.throughput_pts_sec ? `${m.throughput_pts_sec.toLocaleString()} pts/s` : "N/A"}
                  </td>
                  <td className="mono-num" style={{ padding: "12px", fontSize: "0.75rem", color: "var(--text-dim)" }}>
                    {m.git_commit?.substring(0, 7) || "clean"}
                  </td>
                  <td style={{ padding: "12px" }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "3px",
                        fontSize: "0.68rem",
                        fontFamily: "var(--font-mono)",
                        background: isWinner ? "var(--cyan-translucent)" : "rgba(255,255,255,0.05)",
                        color: isWinner ? "var(--cyan-signal)" : "var(--text-dim)",
                        border: `1px solid ${isWinner ? "var(--cyan-signal)" : "var(--panel-border)"}`
                      }}
                    >
                      {m.status || (isWinner ? "Active Baseline" : "Candidate")}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}