"""Images router: Wikimedia search/proxy and PDF image extraction."""

from __future__ import annotations

import base64

import highlight as hlt
import requests
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ..deps import require_session
from ..schemas import (
    PdfImageInfo,
    PdfImagesResponse,
    WikimediaImage,
    WikimediaSearchResponse,
)

router = APIRouter(prefix="/images", tags=["images"])

_USER_AGENT = (
    "PAIGE/1.0 (https://github.com/crvernon/highlight; chris.vernon@pnnl.gov)"
)


@router.get("/wikimedia", response_model=WikimediaSearchResponse)
def wikimedia_search(
    query: str = Query(..., min_length=1),
    limit: int = Query(9, ge=1, le=30),
) -> WikimediaSearchResponse:
    raw = hlt.search_wikimedia_commons(query=query, limit=limit)
    return WikimediaSearchResponse(results=[WikimediaImage(**item) for item in raw])


@router.get("/proxy")
def proxy_image(url: str = Query(..., min_length=1)) -> Response:
    """Fetch an image server-side to avoid client CORS / User-Agent issues."""
    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image URL."
        )
    try:
        resp = requests.get(
            url, timeout=30, headers={"User-Agent": _USER_AGENT}, stream=True
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch image: {exc}",
        ) from exc

    content_type = resp.headers.get("Content-Type", "application/octet-stream")
    return Response(content=resp.content, media_type=content_type)


@router.post("/pdf-extract", response_model=PdfImagesResponse)
def pdf_extract(session_id: str) -> PdfImagesResponse:
    session = require_session(session_id)
    if not session.pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No PDF is associated with this session.",
        )
    extracted = hlt.extract_images_from_pdf(session.pdf_bytes)
    images = []
    for item in extracted:
        b64 = base64.b64encode(item["bytes"]).decode()
        images.append(
            PdfImageInfo(
                index=item["index"],
                page=item["page"],
                data_url=f"data:image/png;base64,{b64}",
                mime="image/png",
            )
        )
    return PdfImagesResponse(images=images)
