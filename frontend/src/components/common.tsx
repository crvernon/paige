import { useState } from "react";

interface TemperatureSliderProps {
  value: number;
  onChange: (v: number) => void;
  label?: string;
}

/**
 * A labelled 0.0–1.0 temperature slider.
 *
 * Note: the OpenAI-compatible endpoint used here does not currently accept a
 * temperature override per request, so this control is retained for parity with
 * the original UI and to communicate intent; the value is sent as guidance only
 * where the backend supports it.
 */
const TEMPERATURE_HINT =
  "Controls how creative or focused the generated text is. Lower values (near 0.0) make the output more focused, deterministic, and repeatable, while higher values (near 1.0) make it more varied and creative.";

export function TemperatureSlider({
  value,
  onChange,
  label = "Set desired temperature:",
}: TemperatureSliderProps) {
  return (
    <div className="mt-2">
      <label className="mb-1 flex items-center gap-1 text-sm text-gray-600">
        <span>{label}</span>
        <span
          className="inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-gray-400 text-xs font-semibold text-gray-500"
          title={TEMPERATURE_HINT}
          aria-label={TEMPERATURE_HINT}
        >
          ?
        </span>
      </label>
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full accent-im3"
        />
        <span className="w-10 text-right text-sm tabular-nums text-gray-700">
          {value.toFixed(1)}
        </span>
      </div>
    </div>
  );
}

interface EditableResultProps {
  value: string;
  onChange: (v: string) => void;
  height?: number;
  placeholder?: string;
}

export function EditableResult({
  value,
  onChange,
  height = 150,
  placeholder,
}: EditableResultProps) {
  return (
    <textarea
      className="textarea mt-3"
      style={{ height }}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

interface GenerateButtonProps {
  onClick: () => void | Promise<void>;
  label: string;
  disabled?: boolean;
}

export function GenerateButton({ onClick, label, disabled }: GenerateButtonProps) {
  const [busy, setBusy] = useState(false);
  return (
    <button
      className="btn mt-3"
      disabled={disabled || busy}
      onClick={async () => {
        setBusy(true);
        try {
          await onClick();
        } finally {
          setBusy(false);
        }
      }}
    >
      {busy ? "Working…" : label}
    </button>
  );
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      {message}
    </div>
  );
}

export function WordCount({ count }: { count: number | null }) {
  if (count === null) return null;
  return <p className="mt-2 text-xs text-gray-500">Word count: {count}</p>;
}
