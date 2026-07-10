# PAIGE Migration Plan: Streamlit → React (Vite/TS/Tailwind) + FastAPI/Pydantic AI

## 1. Goal

Convert the existing Streamlit app ([`app.py`](../app.py)) into a modern JavaScript
application:

- **Frontend**: React + Vite + TypeScript + Tailwind CSS single-page app (SPA), with a
  **white default background**.
- **Backend**: Python FastAPI service using **Pydantic AI** for all LLM interactions and
  keeping the Python-only document generators (`docxtpl`, `python-pptx`, `pymupdf`).
- **LLM provider**: OpenAI-compatible endpoint driven by the updated [`.env`](../.env),
  which now requires an explicit `OPENAI_BASE_URL` (moving off Azure-hosted LLMs).
- **Hosting**: Ubuntu EC2 in production, served via **Nginx + systemd**.

## 2. Why a hybrid (JS frontend + Python backend)

- **Pydantic AI is a Python library** — the AI layer must remain in Python.
- Word/PowerPoint export depends on Python-only libraries (`docxtpl`, `python-pptx`) and
  PDF image extraction uses `pymupdf`. Re-implementing these in JS would be lossy and
  risky (the `.docx`/`.pptx` templates in [`highlight/data/`](../highlight/data) are the
  source of truth).
- The Streamlit UI becomes a React SPA; all state currently held in `st.session_state`
  moves into a client-side store, and all `hlt.*` calls become HTTP requests.

## 3. Target repository layout

```
highlight/
  backend/
    app/
      main.py               # FastAPI app, CORS, routers
      config.py             # Pydantic Settings from .env
      agent.py              # Pydantic AI agents + provider/base_url wiring
      schemas.py            # Request/response Pydantic models
      session.py            # in-memory session store (access + uploaded content)
      routers/
        auth.py             # password / user key validation
        upload.py           # PDF/TXT ingest + stats
        generate.py         # text + structured generation endpoints
        images.py           # wikimedia search/download + pdf image extraction
        export.py           # docx + pptx generation
    highlight/              # refactored library (moved, Streamlit-free)
      __init__.py
      prompts.py            # ported verbatim
      utils.py              # read_pdf/read_text/token count/wikimedia/pdf images
      data/                 # existing .docx / .pptx / im3.png templates
    pyproject.toml
    .env                    # existing credentials (not committed)
  frontend/
    index.html
    package.json
    vite.config.ts
    tailwind.config.js
    src/
      main.tsx
      App.tsx
      api/client.ts         # typed fetch wrapper
      store/appStore.ts     # Zustand (or Context) global state
      components/           # section components (see §6)
      styles/index.css      # Tailwind + white background base
  deploy/
    nginx-paige.conf
    paige-backend.service
    README-deploy.md
  plans/
    paige-js-migration-plan.md
```

## 4. Backend design (FastAPI + Pydantic AI)

### 4.1 Configuration ([`config.py`](../backend/app/config.py))
`Settings(BaseSettings)` reads from `.env`:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (`gpt-5.5-project`)
- `OPENAI_EMBEDDING_MODEL`
- `OPENAI_BASE_URL` (`https://ai-incubator-api.pnnl.gov`) — **required** for the new endpoint
- `IM3_ACCESS` (`phase3`) — the shared unlock password

### 4.2 Pydantic AI agent layer ([`agent.py`](../backend/app/agent.py))
- Build model via `OpenAIModel(model_name, provider=OpenAIProvider(base_url=..., api_key=...))`.
- Factory `build_agent(system_prompt, output_type=None, *, api_key, base_url, model)`:
  - Text agents → `Agent(model, system_prompt=SYSTEM_SCOPE)` returning `str`.
  - Structured agents → `Agent(..., output_type=ApproachPoints | ImpactPoints)` to replace
    the old LangChain `PydanticOutputParser` flow in [`utils.py`](../highlight/utils.py:281).
- Per-request override: when a user pastes their own key + base URL, use those instead of
  the `.env` defaults.
- Prompt strings are reused as-is from [`prompts.py`](../highlight/prompts.py) via a
  `generate_prompt`-style formatter (ported without Streamlit).

### 4.3 Session handling ([`session.py`](../backend/app/session.py))
- On successful auth, mint a `session_id` (UUID) → stores `{api_key, base_url, model}`.
- On upload, store extracted `content` + stats keyed by `session_id` so subsequent
  generation calls don't re-send the full document each time (mirrors `content_dict`).
- In-memory dict is sufficient for a single-instance EC2 deployment (documented as such).

### 4.4 Endpoints (all under `/api`)
| Method | Path | Replaces (Streamlit) |
|---|---|---|
| POST | `/auth` | password / OpenAI key gate (`app.py` lines ~327–371) |
| POST | `/upload` | file uploader + `read_pdf`/`read_text` + stats |
| POST | `/generate/title` | `generate_content("title")` |
| POST | `/generate/subtitle` | `generate_content("subtitle")` |
| POST | `/generate/science` | `generate_content("science")` |
| POST | `/generate/impact` | `generate_content("impact")` |
| POST | `/generate/summary` | `generate_content("summary")` |
| POST | `/generate/citation` | `generate_content("citation")` |
| POST | `/generate/funding` | `generate_content("funding")` |
| POST | `/generate/objective` | `generate_content("objective")` |
| POST | `/generate/search-strings` | `generate_content("figure")` |
| POST | `/generate/image-caption` | `generate_content("figure_caption")` |
| POST | `/generate/figure-list` | `figure_list` prompt |
| POST | `/generate/figure-caption` | `selected_figure_caption` prompt |
| POST | `/generate/approach` | structured `ApproachPoints` |
| POST | `/generate/ppt-impact` | structured `ImpactPoints` |
| GET  | `/images/wikimedia` | `search_wikimedia_commons` |
| GET  | `/images/proxy` | server-side image fetch (avoids CORS/User-Agent issues) |
| POST | `/images/pdf-extract` | `extract_images_from_pdf` (PyMuPDF) |
| POST | `/export/docx` | Word render via `docxtpl` |
| POST | `/export/pptx` | PowerPoint render via `python-pptx` |

- Text endpoints accept `{ session_id, temperature?, max_word_count?, min_word_count? }`
  and return `{ text, word_count }` (word-count reduction logic ported from
  [`generate_content`](../highlight/utils.py:466)).
- Export endpoints accept the assembled field payload + selected image bytes/handle and
  stream back the binary file with the correct `Content-Disposition` filename (the
  citation-based filename logic from `app.py` lines ~1175–1237 moves server-side).

### 4.5 Dependency changes ([`pyproject.toml`](../pyproject.toml))
- **Add**: `fastapi`, `uvicorn[standard]`, `pydantic-ai`, `pydantic-settings`,
  `python-multipart`.
- **Remove**: `streamlit`, `langchain`, `langchain_openai`.
- **Keep**: `openai`, `docxtpl`, `python-pptx`, `pypdf`, `pymupdf`, `tiktoken`,
  `requests`, `tqdm`.

## 5. Frontend design (React + Vite + TS + Tailwind)

### 5.1 Base styling
- Global CSS sets `html, body { background: #ffffff; }` (white default background) and
  Tailwind base layer; content max-width container centered like the current layout.

### 5.2 State store (`store/appStore.ts`)
Holds everything currently in `st.session_state`:
- `access`, `sessionId`, `activeProject`, `model`
- upload stats + `contentReady`
- each generated field (title, subtitle, science, impact, summary, citation, funding,
  objective), editable
- approach/impact bullet arrays (editable lists)
- Wikimedia state (query, results, selected image, caption)
- figure-selection state (figure list, selected id, caption)
- POC dropdown selection + project dictionary

### 5.3 API client (`api/client.ts`)
Typed wrappers for every endpoint in §4.4; attaches `session_id`; helper to trigger binary
downloads for docx/pptx.

## 6. Frontend component map (1:1 with current sections)

1. `Header` — IM3 logo (served by backend) + PAIGE title/subtitle + "How to Use" panel.
2. `AccessGate` — password **or** user OpenAI key + base URL entry → `POST /auth`.
3. `UploadPanel` — file input, shows page/char/word/token stats + token-limit warning.
4. **Word section**:
   - `TitleSection`, `SubtitleSection`, `ScienceSection`, `ImpactSection`,
     `SummarySection` — each with a temperature slider, Generate button, editable
     `textarea`.
   - `CitationSection`, `FundingSection`.
   - `ImageSearchSection` — suggested search strings, Wikimedia query/limit/search,
     results grid with select, selected-image detail, editable caption, full-res download.
   - `PocSection` — project dropdown → POC text.
   - `WordExport` — `POST /export/docx` → download.
5. **PowerPoint section**:
   - `ObjectiveSection`, `ApproachSection` (editable bullet list),
     `PptImpactSection` (editable bullet list).
   - `FigureSelectSection` — list figures, dropdown select, generate/edit caption,
     assign an extracted PDF image.
   - `PptExport` — `POST /export/pptx` → download (guards on title/objective/impact/approach).

## 7. Deployment (Ubuntu EC2, Nginx + systemd)

- **Backend**: `uvicorn app.main:app` managed by systemd unit
  [`paige-backend.service`](../deploy/paige-backend.service), bound to `127.0.0.1:8000`,
  `.env` loaded via `EnvironmentFile`.
- **Frontend**: `npm run build` → static assets served by Nginx.
- **Nginx** ([`nginx-paige.conf`](../deploy/nginx-paige.conf)):
  - serve built SPA at `/` with SPA fallback to `index.html`
  - reverse-proxy `/api/` → `127.0.0.1:8000`
  - reasonable `client_max_body_size` for PDF uploads.
- `deploy/README-deploy.md` documents: install Node + Python, build steps, enabling the
  service, TLS via certbot (optional), and CORS/base-path notes.

## 8. Verification

- Backend unit tests for refactored [`utils.py`](../highlight/utils.py) (PDF/text parsing,
  token count, Wikimedia parsing) and the agent factory (base_url wiring, override path).
- Manual end-to-end pass: auth → upload → generate each field → Wikimedia select →
  export docx → PPT fields → export pptx.

## 9. Open assumptions

- Single-instance backend (in-memory session store) is acceptable for production scale.
- The `.docx`/`.pptx` templates and placeholder names remain unchanged.
- `gpt-5.5-project` is served through the OpenAI-compatible Responses/Chat API at the
  configured base URL; the agent layer will target the standard OpenAI chat interface via
  Pydantic AI's `OpenAIProvider`.
