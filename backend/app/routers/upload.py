"""Upload router: ingest a PDF or text file and store extracted content."""

from __future__ import annotations

import io

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

import highlight as hlt
from ..config import get_settings
from ..deps import require_session
from ..schemas import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> UploadResponse:
    session = require_session(session_id)
    settings = get_settings()

    raw = await file.read()
    content_type = file.content_type or ""
    filename = file.filename or "upload"

    pdf_bytes = None
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        pdf_bytes = raw
        content_dict = hlt.read_pdf(io.BytesIO(raw))
    elif content_type == "text/plain" or filename.lower().endswith(".txt"):
        content_dict = hlt.read_text(io.BytesIO(raw))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload a PDF or text file.",
        )

    # Persist on the session for subsequent generation calls.
    session.content = content_dict["content"]
    session.filename = filename
    session.stats = content_dict
    session.pdf_bytes = pdf_bytes

    return UploadResponse(
        filename=filename,
        n_pages=content_dict["n_pages"],
        n_characters=content_dict["n_characters"],
        n_words=content_dict["n_words"],
        n_tokens=content_dict["n_tokens"],
        max_allowable_tokens=settings.max_allowable_tokens,
        exceeds_limit=content_dict["n_tokens"] > settings.max_allowable_tokens,
        has_pdf_images=pdf_bytes is not None,
    )
