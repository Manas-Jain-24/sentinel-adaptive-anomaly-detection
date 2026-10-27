import { LeaderboardTable } from "../components/LeaderboardTable";
import { RadarChart, ParetoScatter } from "../components/RadarChart";
export function ComparisonView({ results = [], onSelectRun }) {
  if (!results.length) return <div className="glass-panel" style={{padding:"32px",color:"var(--text-muted)"}}><h2 style={{color:"var(--text-white)",marginBottom:"8px"}}>No comparable runs loaded</h2><p>This repository contains one reproducible synthetic smoke run. It does not contain a validated model comparison, so charts and a winner are withheld. Upload compatible run-result JSONL files to compare experiments.</p></div>;
  return <div style={{display:"flex",flexDirection:"column",gap:"20px"}}><LeaderboardTable results={results} onSelectRun={onSelectRun}/><div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"20px"}}><RadarChart results={results}/><ParetoScatter results={results}/></div></div>;
}
