// ComparisonView.jsx
import { LeaderboardTable } from "../components/LeaderboardTable";
import { RadarChart, ParetoScatter } from "../components/RadarChart";

export function ComparisonView({ results = [], onSelectRun }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <LeaderboardTable results={results} onSelectRun={onSelectRun} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        <RadarChart results={results} />
        <ParetoScatter results={results} />
      </div>
    </div>
  );
}