// ManifestView.jsx
import { ManifestView as ManifestComponent } from "../components/ManifestView";

export function ManifestView({ runManifest, predictions }) {
  return <ManifestComponent runManifest={runManifest} predictions={predictions} />;
}