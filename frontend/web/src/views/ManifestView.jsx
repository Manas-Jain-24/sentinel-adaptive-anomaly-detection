// ManifestView.jsx
import { ManifestView as ManifestComponent } from "../components/ManifestView";

export function ManifestView({ runManifest, predictions, predictionsRaw }) {
  return <ManifestComponent runManifest={runManifest} predictions={predictions} predictionsRaw={predictionsRaw} />;
}