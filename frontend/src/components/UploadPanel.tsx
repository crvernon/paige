import { useRef, useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/appStore";

export function UploadPanel() {
  const sessionId = useAppStore((s) => s.sessionId)!;
  const upload = useAppStore((s) => s.upload);
  const reduceContent = useAppStore((s) => s.reduceContent);
  const set = useAppStore((s) => s.set);
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleFile(file: File) {
    setError(null);
    setBusy(true);
    try {
      const res = await api.upload(sessionId, file);
      set("upload", res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h3 className="section-title">Upload file to process</h3>
      <p className="mt-1 text-sm text-gray-600">
        Select a PDF or text file of your publication.
      </p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt"
        className="mt-3 block w-full text-sm text-gray-700 file:mr-4 file:rounded-md file:border-0 file:bg-im3 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-im3-dark"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {busy && <p className="mt-2 text-sm text-gray-500">Processing…</p>}
      {error && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {upload && (
        <div className="mt-4">
          <pre className="whitespace-pre-wrap rounded-md bg-gray-50 p-3 text-xs text-gray-700">
            {`File specs:
- Number of pages:      ${upload.n_pages}
- Number of characters: ${upload.n_characters}
- Number of words:      ${upload.n_words}
- Number of tokens:     ${upload.n_tokens}`}
          </pre>

          {upload.exceeds_limit && (
            <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-3 text-sm text-amber-800">
              <p className="font-semibold">
                🚨 Document exceeds the maximum allowable tokens.
              </p>
              <p className="mt-1">
                Maximum allowable: {upload.max_allowable_tokens} — your document:{" "}
                {upload.n_tokens} (deficit{" "}
                {upload.n_tokens - upload.max_allowable_tokens}). Queries may
                fail. Consider pasting only the relevant sections into a text
                file and re-uploading.
              </p>
              <label className="mt-2 flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={reduceContent}
                  onChange={(e) => set("reduceContent", e.target.checked)}
                />
                Acknowledge and proceed anyway
              </label>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
