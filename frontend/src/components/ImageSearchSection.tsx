import { useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/appStore";
import type { WikimediaImage } from "../api/types";

export function ImageSearchSection() {
  const store = useAppStore();
  const sessionId = store.sessionId!;
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(9);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const results = store.wikimediaResults;
  const selected = store.selectedImage;

  const defaultQuery =
    store.suggestedSearchStrings.split("\n")[0]?.trim() ||
    store.title ||
    store.summary.split(/\s+/).slice(0, 15).join(" ");

  async function suggest() {
    if (!store.summary) return;
    setError(null);
    try {
      const res = await api.generate("search-strings", {
        sessionId,
        contentOverride: store.summary,
      });
      store.set("suggestedSearchStrings", res.text.replace(/"/g, ""));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function search() {
    const q = query || defaultQuery;
    if (!q) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.wikimedia(q, limit);
      store.set("wikimediaResults", res.results);
      store.set("selectedImage", null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function selectImage(img: WikimediaImage) {
    store.set("selectedImage", img);
  }

  async function suggestCaption() {
    setError(null);
    try {
      const res = await api.generate("image-caption", {
        sessionId,
        maxWordCount: 30,
        minWordCount: 10,
      });
      store.set("imageCaption", res.text);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <section className="card">
      <h3 className="section-title">Find an image for your Word document</h3>
      <p className="mt-1 text-sm text-gray-600">
        Editorial cover image from Wikimedia Commons (fully open and reusable).
        This is <em>not</em> a figure from your paper.
      </p>

      <div className="mt-4">
        <button
          className="btn-secondary"
          disabled={!store.summary}
          onClick={suggest}
        >
          Suggest search strings
        </button>
        {!store.summary && (
          <p className="mt-1 text-xs text-amber-700">
            Generate the general summary first to enable suggestions.
          </p>
        )}
        {store.suggestedSearchStrings && (
          <textarea
            className="textarea mt-2"
            style={{ height: 120 }}
            readOnly
            value={store.suggestedSearchStrings.replace(/"/g, "")}
          />
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div className="flex-1">
          <label className="mb-1 block text-sm text-gray-700">
            Image search query
          </label>
          <input
            className="input"
            value={query}
            placeholder={defaultQuery}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="w-28">
          <label className="mb-1 block text-sm text-gray-700">Max results</label>
          <input
            type="number"
            min={3}
            max={30}
            step={3}
            className="input"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          />
        </div>
        <button className="btn" disabled={busy} onClick={search}>
          {busy ? "Searching…" : "Search"}
        </button>
      </div>

      {error && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {results && !selected && (
        <div className="mt-4 grid max-h-[500px] grid-cols-2 gap-4 overflow-y-auto rounded-md border border-gray-200 p-3 sm:grid-cols-3">
          {results.map((img) => (
            <div key={img.id ?? img.title} className="text-center">
              {img.thumbnail_url && (
                <img
                  src={img.thumbnail_url}
                  alt={img.title}
                  className="mx-auto h-32 object-contain"
                />
              )}
              <p className="mt-1 truncate text-xs text-gray-600" title={img.title}>
                {img.title} ({img.license || "N/A"})
              </p>
              <button
                className="btn-secondary mt-2 text-xs"
                onClick={() => selectImage(img)}
              >
                Select this image
              </button>
            </div>
          ))}
        </div>
      )}

      {selected && (
        <div className="mt-4 rounded-md border border-gray-200 p-4">
          <div className="flex gap-4">
            {selected.thumbnail_url && (
              <img
                src={selected.thumbnail_url}
                alt={selected.title}
                className="h-32 object-contain"
              />
            )}
            <div className="text-sm text-gray-700">
              <p>
                <span className="font-semibold">Title:</span> {selected.title}
              </p>
              <p>
                <span className="font-semibold">License:</span>{" "}
                {selected.license || "N/A"}
              </p>
              {selected.page_url && (
                <p>
                  <span className="font-semibold">Source:</span>{" "}
                  <a
                    className="text-im3 underline"
                    href={selected.page_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {selected.page_url}
                  </a>
                </p>
              )}
              <button
                className="btn-secondary mt-2 text-xs"
                onClick={() => store.set("selectedImage", null)}
              >
                Change selection
              </button>
            </div>
          </div>

          <div className="mt-4">
            <button className="btn-secondary" onClick={suggestCaption}>
              Suggest caption
            </button>
            <textarea
              className="textarea mt-2"
              style={{ height: 100 }}
              placeholder="Enter caption or generate a suggestion…"
              value={store.imageCaption}
              onChange={(e) => store.set("imageCaption", e.target.value)}
            />
          </div>
        </div>
      )}
    </section>
  );
}
