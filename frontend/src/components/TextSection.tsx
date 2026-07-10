import { useState } from "react";
import { api } from "../api/client";
import { useAppStore, type AppState } from "../store/appStore";
import {
  EditableResult,
  ErrorNote,
  GenerateButton,
  TemperatureSlider,
  WordCount,
} from "./common";

interface TextSectionProps {
  title: string;
  description: React.ReactNode;
  endpoint: string;
  stateKey: keyof AppState;
  buttonLabel: string;
  defaultTemperature?: number;
  height?: number;
  maxWordCount?: number;
  minWordCount?: number;
  // Provide extra context (e.g. the current title for the subtitle prompt).
  getAdditionalContent?: (s: AppState) => string | undefined;
  // Provide a content override (e.g. summary text for search-string generation).
  getContentOverride?: (s: AppState) => string | undefined;
  // Require another field to be present before enabling generation.
  requires?: { key: keyof AppState; message: string };
  // Optional post-processing of the returned text.
  transform?: (text: string) => string;
}

/**
 * Generic "generate + edit" section used by the Word/PowerPoint text fields.
 */
export function TextSection({
  title,
  description,
  endpoint,
  stateKey,
  buttonLabel,
  defaultTemperature = 0.3,
  height = 200,
  maxWordCount,
  minWordCount,
  getAdditionalContent,
  getContentOverride,
  requires,
  transform,
}: TextSectionProps) {
  const store = useAppStore();
  const sessionId = store.sessionId!;
  const value = (store[stateKey] as string) || "";
  const [temperature, setTemperature] = useState(defaultTemperature);
  const [wordCount, setWordCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setError(null);
    if (requires && !((store[requires.key] as string) || "").trim()) {
      setError(requires.message);
      return;
    }
    try {
      const state = useAppStore.getState();
      const res = await api.generate(endpoint, {
        sessionId,
        additionalContent: getAdditionalContent?.(state),
        contentOverride: getContentOverride?.(state),
        maxWordCount,
        minWordCount,
      });
      const text = transform ? transform(res.text) : res.text;
      store.set(stateKey, text as never);
      setWordCount(text.split(/\s+/).filter(Boolean).length);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <section className="card">
      <h3 className="section-title">{title}</h3>
      <div className="mt-2 text-sm text-gray-600">{description}</div>
      <TemperatureSlider value={temperature} onChange={setTemperature} />
      <GenerateButton onClick={handleGenerate} label={buttonLabel} />
      <ErrorNote message={error} />
      {value && (
        <>
          <EditableResult
            value={value}
            height={height}
            onChange={(v) => store.set(stateKey, v as never)}
          />
          <WordCount count={wordCount} />
        </>
      )}
    </section>
  );
}
