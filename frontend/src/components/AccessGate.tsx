import { useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/appStore";

export function AccessGate() {
  const setAuth = useAppStore((s) => s.setAuth);
  const setProjects = useAppStore((s) => s.set);
  const [mode, setMode] = useState<"password" | "key">("password");
  const [password, setPassword] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      const res = await api.auth(
        mode === "password"
          ? { password }
          : { apiKey, baseUrl: baseUrl || undefined, model: model || undefined }
      );
      setAuth({
        sessionId: res.session_id,
        activeProject: res.active_project,
        model: res.model,
        maxAllowableTokens: res.max_allowable_tokens,
      });
      try {
        const projects = await api.projects();
        setProjects("projects", projects.projects);
      } catch {
        // non-fatal
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto mt-8 max-w-md">
      <div className="card">
        <h2 className="section-title">Sign in</h2>
        <p className="mt-1 text-sm text-gray-600">
          Enter your project password, or provide your own OpenAI-compatible API
          key and base URL.
        </p>

        <div className="mt-4 flex gap-2">
          <button
            className={mode === "password" ? "btn" : "btn-secondary"}
            onClick={() => setMode("password")}
          >
            Project password
          </button>
          <button
            className={mode === "key" ? "btn" : "btn-secondary"}
            onClick={() => setMode("key")}
          >
            API key
          </button>
        </div>

        {mode === "password" ? (
          <div className="mt-4">
            <label className="mb-1 block text-sm text-gray-700">
              Project password
            </label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            <div>
              <label className="mb-1 block text-sm text-gray-700">
                OpenAI API key
              </label>
              <input
                type="password"
                className="input"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-700">
                Base URL
              </label>
              <input
                type="text"
                className="input"
                placeholder="https://ai-incubator-api.pnnl.gov"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-700">
                Model (optional)
              </label>
              <input
                type="text"
                className="input"
                placeholder="gpt-5.5-project"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <button className="btn mt-4 w-full" disabled={busy} onClick={submit}>
          {busy ? "Verifying…" : "Unlock PAIGE"}
        </button>
      </div>
    </div>
  );
}
