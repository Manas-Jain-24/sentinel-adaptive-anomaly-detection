// FiguresView.jsx
import { FigureShelf } from "../components/ManifestView";

export function FiguresView({ figures, onDownload }) {
  return <FigureShelf figures={figures} onDownload={onDownload} />;
}