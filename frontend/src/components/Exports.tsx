import { useState } from "react";
import { api, downloadBlob } from "../api/client";
import { useAppStore } from "../store/appStore";

export function WordExport() {
  const store = useAppStore();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function exportDoc() {
    setBusy(true);
    setError(null);
    try {
      const selected = store.selectedImage;
      const blob = await api.exportDocx({
        sessionId: store.sessionId!,
        title: store.title,
        subtitle: store.subtitle,
        imageCaption: store.imageCaption,
        science: store.science,
        impact: store.impact,
        summary: store.summary,
        funding: store.funding,
        citation: store.citation,
        pointOfContact: store.pointOfContact,
        selectedImage: selected
          ? {
              full_url: selected.full_url,
              page_url: selected.page_url,
              artist_plain: selected.artist_plain,
              license: selected.license,
              license_url: selected.license_url,
            }
          : null,
      });
      downloadBlob(blob, "ber-highlight.docx");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h3 className="section-title">Export Word document</h3>
      <p className="mt-1 text-sm text-gray-600">
        Generate the Word document with the content produced above.
      </p>
      <button className="btn mt-3" disabled={busy} onClick={exportDoc}>
        {busy ? "Generating…" : "Export Word document"}
      </button>
      {error && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
    </section>
  );
}

export function PptExport() {
  const store = useAppStore();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const ready =
    store.title &&
    store.objective &&
    store.pptImpactPoints.length > 0 &&
    store.approachPoints.length > 0;

  async function exportPpt() {
    setBusy(true);
    setError(null);
    try {
      const blob = await api.exportPptx({
        sessionId: store.sessionId!,
        title: store.title,
        objective: store.objective,
        citation: store.citation,
        figureCaption: store.figureCaption,
        approachPoints: store.approachPoints,
        impactPoints: store.pptImpactPoints,
        figureImageIndex: store.selectedFigureImageIndex,
      });
      downloadBlob(blob, "ber-highlight.pptx");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h3 className="section-title">Export PowerPoint presentation</h3>
      {!ready && (
        <p className="mt-1 text-sm text-amber-700">
          ⚠️ Generate the title, objective, impact, and approach content before
          exporting.
        </p>
      )}
      <button className="btn mt-3" disabled={busy || !ready} onClick={exportPpt}>
        {busy ? "Generating…" : "Export PowerPoint presentation"}
      </button>
      {error && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
    </section>
  );
}
