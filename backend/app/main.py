"""PAIGE FastAPI application entry point.

Wires together the routers, CORS, logging, and a POC lookup endpoint.
Run in development with::

    uvicorn app.main:app --reload --port 8000

from within the ``backend`` directory.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .deps import PROJECT_DICT
from .routers import auth, export, generate, images, misc, upload

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="PAIGE API",
    description="PNNL AI assistant for GEnerating publication highlights.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"

app.include_router(misc.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(upload.router, prefix=API_PREFIX)
app.include_router(generate.router, prefix=API_PREFIX)
app.include_router(images.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/projects")
def projects() -> dict:
    """Return the point-of-contact directory for the POC dropdown."""
    return {"projects": PROJECT_DICT}
