import { useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/appStore";

export function FigureSelectSection() {
  const store = useAppStore();
  const sessionId = store.sessionId!;
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const figures = store.figures;
  const selectedId = store.selectedFigureId;
  const pdfImages = store.pdfImages;

  async function listFigures() {
    setBusy(true);
    setError(null);
    try {
      const res = await api.figureList({ sessionId });
      store.set("figures", res.figures);
      store.set("selectedFigureId", null);
      store.set("figureCaption", "");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function suggestCaption() {
    if (!selectedId) return;
    setError(null);
    try {
      const res = await api.generate("figure-caption", {
        sessionId,
        additionalContent: selectedId,
      });
      store.set("figureCaption", res.text.trim());
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function loadPdfImages() {
    setBusy(true);
    setError(null);
    try {
      const res = await api.pdfExtract(sessionId);
      store.set("pdfImages", res.images);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h3 className="section-title">
        Select figure and generate caption for PowerPoint
      </h3>

      <button className="btn-secondary mt-3" disabled={busy} onClick={listFigures}>
        List figures from text
      </button>

      {error && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {figures && Object.keys(figures).length > 0 && (
        <div className="mt-4">
          <label className="mb-1 block text-sm text-gray-700">
            Choose the figure ID for the slide:
          </label>
          <select
            className="input"
            value={selectedId ?? ""}
            onChange={(e) => {
              store.set("selectedFigureId", e.target.value || null);
              store.set("figureCaption", "");
            }}
          >
            <option value="">&lt;Select a figure ID&gt;</option>
            {Object.entries(figures).map(([id, desc]) => (
              <option key={id} value={id}>
                {id}: {desc}
              </option>
            ))}
          </select>
        </div>
      )}

      {selectedId && (
        <div className="mt-4">
          <button className="btn-secondary" onClick={suggestCaption}>
            Suggest caption for {selectedId}
          </button>
          <textarea
            className="textarea mt-2"
            style={{ height: 100 }}
            placeholder={`Enter caption for ${selectedId} or generate a suggestion…`}
            value={store.figureCaption}
            onChange={(e) => store.set("figureCaption", e.target.value)}
          />
        </div>
      )}

      {store.upload?.has_pdf_images && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-gray-800">
            Assign an image extracted from the PDF (optional)
          </h4>
          <button
            className="btn-secondary mt-2"
            disabled={busy}
            onClick={loadPdfImages}
          >
            Load images from PDF
          </button>

          {pdfImages && pdfImages.length > 0 && (
            <div className="mt-3 grid max-h-[400px] grid-cols-2 gap-3 overflow-y-auto rounded-md border border-gray-200 p-3 sm:grid-cols-4">
              {pdfImages.map((img) => (
                <div key={img.index} className="text-center">
                  <img
                    src={img.data_url}
                    alt={`PDF image ${img.index}`}
                    className={`mx-auto h-24 object-contain ${
                      store.selectedFigureImageIndex === img.index
                        ? "ring-2 ring-im3"
                        : ""
                    }`}
                  />
                  <p className="text-xs text-gray-500">page {img.page}</p>
                  <button
                    className="btn-secondary mt-1 text-xs"
                    onClick={() =>
                      store.set("selectedFigureImageIndex", img.index)
                    }
                  >
                    {store.selectedFigureImageIndex === img.index
                      ? "Assigned"
                      : "Assign"}
                  </button>
                </div>
              ))}
            </div>
          )}
          {pdfImages && pdfImages.length === 0 && (
            <p className="mt-2 text-sm text-gray-500">
              No embedded images found in the PDF.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
