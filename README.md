[![build](https://github.com/crvernon/highlight/actions/workflows/build.yml/badge.svg)](https://github.com/crvernon/highlight/actions/workflows/build.yml)
[![DOI](https://zenodo.org/badge/632456925.svg)](https://zenodo.org/doi/10.5281/zenodo.13750915)


## highlight — PAIGE

#### Generate publication highlights using AI

PAIGE (the PNNL AI assistant for GEnerating publication highlights) is now a
**modern JavaScript application**: a React + Vite + TypeScript + Tailwind
single-page app backed by a **FastAPI + [Pydantic AI](https://ai.pydantic.dev/)**
service. It takes a publication (PDF or text) and drafts a Word highlight
document and a PowerPoint slide.

> The previous Streamlit app (`app.py`) has been retired. See
> [`plans/paige-js-migration-plan.md`](plans/paige-js-migration-plan.md) for the
> migration details.

### Architecture

```
frontend/   React + Vite + TypeScript + Tailwind SPA (white default background)
backend/    FastAPI service; all AI runs through Pydantic AI
highlight/  Shared Python library (PDF/text parsing, prompts, Word/PPT templates)
deploy/     Nginx config + systemd unit for Ubuntu EC2
```

The AI layer targets an **OpenAI-compatible endpoint** (moved off the Azure
deployments). The new endpoint requires an explicit **base URL**.

### Configuration

Create a `.env` in the repository root (and copy it to `backend/.env` for
deployment):

```dotenv
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-5.5-project"
OPENAI_EMBEDDING_MODEL="text-embedding-3-large-project"
OPENAI_BASE_URL="https://ai-incubator-api.pnnl.gov"
IM3_ACCESS="phase3"
```

Users sign in with the `IM3_ACCESS` password, or by supplying their own
OpenAI-compatible API key and base URL in the sign-in screen.

### Local development

**Backend** (from the repository root):

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install .
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend** (in a second terminal):

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on `http://localhost:5173` and proxies `/api` to the
backend on port 8000.

### Production (Ubuntu EC2)

The app is served in production by **Nginx** (static SPA + `/api` reverse proxy)
with the backend managed by **systemd**. Full instructions are in
[`deploy/README-deploy.md`](deploy/README-deploy.md).

### Tests

```bash
pip install ".[test]"
pytest
```
