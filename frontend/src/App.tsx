import { useState } from "react";
import { useAppStore } from "./store/appStore";
import { AccessGate } from "./components/AccessGate";
import { UploadPanel } from "./components/UploadPanel";
import { TextSection } from "./components/TextSection";
import { BulletSection } from "./components/BulletSection";
import { ImageSearchSection } from "./components/ImageSearchSection";
import { PocSection } from "./components/PocSection";
import { FigureSelectSection } from "./components/FigureSelectSection";
import { WordExport, PptExport } from "./components/Exports";

function Header() {
  const logout = useAppStore((s) => s.logout);
  const sessionId = useAppStore((s) => s.sessionId);
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="relative mx-auto flex max-w-4xl items-center justify-center px-4 py-5">
        {/* IM3 logo, top-left */}
        <a
          href="https://im3.pnnl.gov/"
          target="_blank"
          rel="noreferrer"
          className="absolute left-4 top-1/2 -translate-y-1/2"
        >
          <img src="/im3_logo.png" alt="IM3 Logo" className="h-12 w-auto" />
        </a>

        {/* PAIGE wordmark, centered */}
        <img
          src="/paige_logo.png"
          alt="PAIGE — The PNNL AI assistant for GEnerating publication highlights"
          className="h-48 w-auto"
        />

        {sessionId && (
          <button
            className="btn-secondary absolute right-4 top-4 text-xs"
            onClick={logout}
          >
            Sign out
          </button>
        )}
      </div>
    </header>
  );
}

function HowToUse() {
  const [open, setOpen] = useState(false);
  return (
    <section className="card">
      <button
        className="flex w-full items-center justify-between text-left"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="section-title">How to use PAIGE</span>
        <span className="text-gray-500">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-gray-600">
          <li>Enter your project password or OpenAI API key.</li>
          <li>Load the PDF or text of your publication into the app.</li>
          <li>Generate each part of your document in order.</li>
          <li>Export the Word document.</li>
          <li>Repeat to generate the PowerPoint slide.</li>
        </ol>
      )}
    </section>
  );
}

export default function App() {
  const sessionId = useAppStore((s) => s.sessionId);
  const upload = useAppStore((s) => s.upload);
  const store = useAppStore();

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main className="mx-auto max-w-4xl space-y-5 px-4 py-6">
        <HowToUse />

        {!sessionId && <AccessGate />}

        {sessionId && (
          <>
            <UploadPanel />

            {upload && (
              <>
                <h2 className="pt-2 text-xl font-bold text-gray-900">
                  Section 1 — Word document content
                </h2>

                <TextSection
                  title="Title"
                  buttonLabel="Generate title"
                  endpoint="title"
                  stateKey="title"
                  defaultTemperature={0.2}
                  height={75}
                  description="A one-sentence, colon-free title (max 10 words) for a general audience."
                />

                <TextSection
                  title="Subtitle"
                  buttonLabel="Generate subtitle"
                  endpoint="subtitle"
                  stateKey="subtitle"
                  defaultTemperature={0.5}
                  height={75}
                  maxWordCount={100}
                  minWordCount={75}
                  requires={{
                    key: "title",
                    message:
                      "Please generate a title first. The subtitle considers the title.",
                  }}
                  getAdditionalContent={(s) => s.title}
                  description="An extension of the title (≤155 characters) that entices the reader."
                />

                <TextSection
                  title="Science summary"
                  buttonLabel="Generate science summary"
                  endpoint="science"
                  stateKey="science"
                  defaultTemperature={0.3}
                  height={200}
                  maxWordCount={100}
                  minWordCount={75}
                  description="Describe the scientific results for a non-expert audience (75–100 words)."
                />

                <TextSection
                  title="Impact summary"
                  buttonLabel="Generate impact summary"
                  endpoint="impact"
                  stateKey="impact"
                  defaultTemperature={0.0}
                  height={200}
                  maxWordCount={100}
                  minWordCount={75}
                  description="Describe the impact of the research for a non-expert audience (75–100 words)."
                />

                <TextSection
                  title="General summary"
                  buttonLabel="Generate general summary"
                  endpoint="summary"
                  stateKey="summary"
                  defaultTemperature={0.3}
                  height={300}
                  maxWordCount={200}
                  minWordCount={100}
                  description="A 1–2 paragraph general summary (≤200 words)."
                />

                <TextSection
                  title="Citation (Chicago style)"
                  buttonLabel="Generate citation"
                  endpoint="citation"
                  stateKey="citation"
                  height={150}
                  description="Generated only from what is present in the publication."
                />

                <ImageSearchSection />

                <TextSection
                  title="Funding statement"
                  buttonLabel="Generate funding statement"
                  endpoint="funding"
                  stateKey="funding"
                  height={150}
                  description="Extracted from the publication. Review thoroughly for accuracy."
                />

                <PocSection />

                <WordExport />

                <h2 className="pt-4 text-xl font-bold text-gray-900">
                  Section 2 — PowerPoint content
                </h2>

                <TextSection
                  title="Objective"
                  buttonLabel="Generate objective"
                  endpoint="objective"
                  stateKey="objective"
                  defaultTemperature={0.3}
                  height={120}
                  description="One sentence stating the core purpose of the study."
                />

                <BulletSection
                  title="Approach"
                  buttonLabel="Generate approach"
                  endpoint="approach"
                  stateKey="approachPoints"
                  defaultTemperature={0.1}
                  requires={{
                    key: "objective",
                    message: "Please generate the objective first.",
                  }}
                  getAdditionalContent={(s) => s.objective}
                  description="2–3 methodological points that accomplish the objective."
                />

                <BulletSection
                  title="Impact points"
                  buttonLabel="Generate impact points"
                  endpoint="ppt-impact"
                  stateKey="pptImpactPoints"
                  defaultTemperature={0.1}
                  description="3 concise points stating key results and outcomes."
                />

                <FigureSelectSection />

                <PptExport />
              </>
            )}

            {/* Keep the store referenced to appease strict unused checks. */}
            <span className="hidden">{store.model}</span>
          </>
        )}
      </main>
    </div>
  );
}
