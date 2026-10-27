import { useState, useEffect } from "react";
import { parsePredictionsJsonl, parseRunJson, parseWindowsJson, parseEvaluationJson, parseResults } from "../lib/parsers";

export function useRunData() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [predictionsRaw, setPredictionsRaw] = useState("");
  const [runManifest, setRunManifest] = useState(null);
  const [windows, setWindows] = useState([]);
  const [evaluation, setEvaluation] = useState(null);
  const [modelResults, setModelResults] = useState([]);
  const [sourceName, setSourceName] = useState("Bundled Demo Run");
  const [selectedSeries, setSelectedSeries] = useState("all");
  const [seriesList, setSeriesList] = useState([]);

  // Load bundled demo artifacts on start
  useEffect(() => {
    async function loadBundled() {
      try {
        setLoading(true);
        const [pRes, rRes, wRes, eRes, resRes] = await Promise.all([
          fetch("/demo/predictions.jsonl"),
          fetch("/demo/run.json"),
          fetch("/demo/windows.json"),
          fetch("/demo/evaluation.json"),
          fetch("/demo/results.jsonl")
        ]);

        if (!pRes.ok || !rRes.ok) {
          throw new Error("Failed to load demo artifacts from public/demo/");
        }

        const [pText, rJson, wJson, eJson, resText] = await Promise.all([
          pRes.text(),
          rRes.json(),
          wRes.ok ? wRes.json() : null,
          eRes.ok ? eRes.json() : null,
          resRes.ok ? resRes.text() : null
        ]);

        const parsedPredictions = parsePredictionsJsonl(pText);
        const parsedManifest = parseRunJson(rJson);
        const parsedWindows = parseWindowsJson(wJson);
        const parsedEval = parseEvaluationJson(eJson);
        const parsedResults = resText ? parseResults(resText) : [];

        setPredictions(parsedPredictions);
        setPredictionsRaw(pText);
        setRunManifest(parsedManifest);
        setWindows(parsedWindows);
        setEvaluation(parsedEval);
        setModelResults(parsedResults);

        const series = Array.from(new Set(parsedPredictions.map(p => p.series_id)));
        setSeriesList(series);
        if (series.length > 0) setSelectedSeries(series[0]);
        setSourceName("Synthetic Smoke Run (Bundled)");
        setLoading(false);
      } catch (err) {
        console.error("Error loading bundled demo data:", err);
        setError(err.message);
        setLoading(false);
      }
    }
    loadBundled();
  }, []);

  // Handle file uploads (predictions.jsonl, run.json, windows.json, etc.)
  const loadCustomFiles = async (files) => {
    try {
      setLoading(true);
      setError(null);
      for (const file of files) {
        const text = await file.text();
        if (file.name.endsWith(".jsonl")) {
          if (file.name.includes("result")) {
            setModelResults(parseResults(text));
          } else {
            const preds = parsePredictionsJsonl(text);
            setPredictions(preds);
            setPredictionsRaw(text);
            const series = Array.from(new Set(preds.map(p => p.series_id)));
            setSeriesList(series);
            if (series.length > 0) setSelectedSeries(series[0]);
          }
        } else if (file.name.endsWith(".json")) {
          try {
            const json = JSON.parse(text);
            if (json.windows || Array.isArray(json)) {
              setWindows(parseWindowsJson(json));
            } else if (json.metric_id || json.event_f1 !== undefined) {
              setEvaluation(parseEvaluationJson(json));
            } else if (json.schema_version && json.algorithm) {
              setRunManifest(parseRunJson(json));
            }
          } catch (e) {
            console.error("Invalid JSON file:", file.name, e);
          }
        } else if (file.name.endsWith(".csv")) {
          setModelResults(parseResults(text));
        }
      }
      setSourceName(`Custom Upload (${files.length} files)`);
      setLoading(false);
    } catch (e) {
      setError(`Failed to parse uploaded files: ${e.message}`);
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    predictions,
    predictionsRaw,
    runManifest,
    windows,
    evaluation,
    modelResults,
    sourceName,
    selectedSeries,
    setSelectedSeries,
    seriesList,
    loadCustomFiles
  };
}