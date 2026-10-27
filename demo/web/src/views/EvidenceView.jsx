// EvidenceView.jsx
import { AnatomyDiagram } from "../components/AnatomyDiagram";

export function EvidenceView({ predictions = [], windows = [], selectedPoint = null, onSelectPoint }) {
  return (
    <AnatomyDiagram
      predictions={predictions}
      windows={windows}
      selectedPoint={selectedPoint}
      onSelectPoint={onSelectPoint}
    />
  );
}