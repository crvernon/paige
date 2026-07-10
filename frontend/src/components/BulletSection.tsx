import { useState } from "react";
import { api } from "../api/client";
import { useAppStore, type AppState } from "../store/appStore";
import { ErrorNote, GenerateButton, TemperatureSlider } from "./common";

interface BulletSectionProps {
  title: string;
  description: React.ReactNode;
  endpoint: string; // "approach" | "ppt-impact"
  stateKey: keyof AppState; // "approachPoints" | "pptImpactPoints"
  buttonLabel: string;
  defaultTemperature?: number;
  getAdditionalContent?: (s: AppState) => string | undefined;
  requires?: { key: keyof AppState; message: string };
}

/**
 * Structured bullet-point section (approach / impact points). Results are shown
 * in an editable textarea, one bullet per line, and parsed back to an array.
 */
export function BulletSection({
  title,
  description,
  endpoint,
  stateKey,
  buttonLabel,
  defaultTemperature = 0.1,
  getAdditionalContent,
  requires,
}: BulletSectionProps) {
  const store = useAppStore();
  const sessionId = store.sessionId!;
  const points = (store[stateKey] as string[]) || [];
  const [temperature, setTemperature] = useState(defaultTemperature);
  const [error, setError] = useState<string | null>(null);

  const textValue = points
    .map((p) => (p.trim().startsWith("-") ? p.trim() : `- ${p.trim()}`))
    .join("\n");

  function updateFromText(text: string) {
    const list = text
      .split("\n")
      .map((line) => line.trim().replace(/^-\s*/, ""))
      .filter(Boolean);
    store.set(stateKey, list as never);
  }

  async function handleGenerate() {
    setError(null);
    if (requires && !((store[requires.key] as string) || "").trim()) {
      setError(requires.message);
      return;
    }
    try {
      const state = useAppStore.getState();
      const res = await api.structured(endpoint, {
        sessionId,
        additionalContent: getAdditionalContent?.(state),
      });
      store.set(stateKey, res.points as never);
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
      {points.length > 0 && (
        <textarea
          className="textarea mt-3"
          style={{ height: 200 }}
          value={textValue}
          onChange={(e) => updateFromText(e.target.value)}
        />
      )}
    </section>
  );
}
