// OverviewView.jsx
import { LandingHeroWaveform } from "../components/LandingHeroWaveform";

export function OverviewView({ onNavigate, kpis }) {
  return <LandingHeroWaveform onNavigate={onNavigate} kpis={kpis} />;
}